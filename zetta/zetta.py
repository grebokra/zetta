import os
import sys
import datetime
import argparse
import shutil
from subprocess import call
from git import Repo
from git import GitCommandError
from git import InvalidGitRepositoryError

def parse_args():
    parser = argparse.ArgumentParser(
        description="A Tool for managing a \"box of notes\"")
    subparsers = parser.add_subparsers(dest="action")
    
    search_parser = subparsers.add_parser("search",
            help="search through notes")
    search_parser.add_argument("pattern", type=str,
            help="pattern to search in notes for")

    edit_parser = subparsers.add_parser("edit",
            help="edit note by id")
    edit_parser.add_argument("id",
            help="note id")
    
    create_parser = subparsers.add_parser("create",
            help="create new note")
    create_parser.add_argument("-t", "--title", type=str,
            default="# ", dest="title", help="desired title")

    delete_parser = subparsers.add_parser("delete",
            help="delete note by id")
    delete_parser.add_argument("id",
            help="note id")
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    try:
        global PATH_TO_REPO
        PATH_TO_REPO = os.environ["ZETTA_BOX"]
    except KeyError as e:
        sys.stderr.write("Error: please set ZETTA_BOX environment variable\nto path to git repo to store notes in!\n\n")
        return -1

    if not (os.path.exists(PATH_TO_REPO) and os.path.isdir(PATH_TO_REPO)):
        sys.stderr.write("Error: path to repo is invalid!\n\n")
        return -1
        
        global REPO
    try:
        REPO = Repo(PATH_TO_REPO)
    except InvalidGitRepositoryError as e:
        sys.stderr.write("Error: path in ZETTA_BOX is a valid path to dir, but there isn't a git repo in it\n\n")
        return -1

    actions = {
        "search": search,
        "edit": edit,
        "create": create,
        "delete": delete
    }
    
    if args.action in actions.keys():
        action = actions[args.action]
        if callable(action):
            action(args)
    
def search(args):
    pattern_lower = args.pattern.lower()
    notes = os.listdir(PATH_TO_REPO)[1:]
    for note_name in notes:
        path = f'{PATH_TO_REPO}{note_name}'
        path_to_note_file = f"{path}/README.md"
        with open(path_to_note_file, 'r') as note_file:
            title = note_file.readline()
            if "\n" in title:
                title = title[:-1]
            if "#" in title:
                title = title[1:]
                title = title.strip()
            note_file.seek(0)
            while True:
                line = note_file.readline()
                line = line.lower()
                if not line:
                    break
                if pattern_lower in line:
                    print(note_name + ": " + title)
                    break

def edit(args):
    note_name = args.id
    editor = os.environ.get("EDITOR") if os.environ.get("EDITOR") else "vi"
    path = f'{PATH_TO_REPO}{os.path.sep}{note_name}'
    path_to_note_file = f"{path}/README.md"
    
    call([editor, path_to_note_file])
    with open(path_to_note_file, "r") as note_file:
        commit_message = note_name + ": " + note_file.readline()

    commit = input("commit? (y/n): ")
    while (commit != "y") and (commit != "n"):
        commit = input("enter either \"y\" or \"n\": ")\

    if (commit == "y"):
        git = REPO.git
        git.add(path_to_note_file)
        try:
            git.commit(m=commit_message)
        except GitCommandError as e:
            print("Nothing to commit :(\n")

def create(args):
    title = str(args.title)
    editor = os.environ.get("EDITOR") if os.environ.get("EDITOR") else "vi"
    note_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    path = f'{PATH_TO_REPO}{os.path.sep}{note_name}'
    os.mkdir(path)
    path_to_note_file = f"{path}/README.md"
    with open(path_to_note_file, "w") as note_file:
        note_file.write(title)
        note_file.flush()
        call([editor, path_to_note_file])
        
        note_file = open(path_to_note_file, "r") 
        commit_message = note_name + ": " + note_file.readline()
    
    print(note_name)
    commit = input("commit? (y/n): ")
    while (commit != "y") and (commit != "n"):
        commit = input("enter either \"y\" or \"n\": ")\
    
    if (commit == "y"):
        git = REPO.git
        git.add(path_to_note_file)
        git.commit(m=commit_message)
    

def delete(args):
    note_name = args.id
    path = f'{PATH_TO_REPO}{os.path.sep}{note_name}'
    path_to_note_file = f"{path}/README.md"
    try:
        with open(path_to_note_file, "r") as note_file:
            note_title = note_file.readline()
    except FileNotFoundError as e:
        sys.stderr.write("\nError: note with given name does not exist :(\n\n")
        return

    do_deletion = input(f"{note_name}: {note_title}\ndelete? (y/n): ")
    
    if (do_deletion != "y"):
        print("deletion canceled!")
        return

    shutil.rmtree(path)
    commit_message = "deleted " + note_name
    print(f"deleted {note_name} ({note_title})")
    commit = input("commit? (y/n): ")
    while (commit != "y") and (commit != "n"):
        commit = input("enter either \"y\" or \"n\": ")\

    if (commit == "y"):
        try:
            git = REPO.git
            git.add(path_to_note_file)
            git.commit(m=commit_message)
        except GitCommandError as e:
            sys.stderr.write("\nWarning: could not commit note deletion (was not committed on creation?)\n\n")


if __name__ == "__main__":
    exit(main())
