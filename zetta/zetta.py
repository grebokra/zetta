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

    show_parser = subparsers.add_parser("show",
            help="show note by id")
    show_parser.add_argument("id",
            help="note id")

    list_parser = subparsers.add_parser("list",
            help="list all notes")

    # returns args but if none were given the arg is --help
    return parser.parse_args(args=None if sys.argv[1:] else ['--help'])


def main():
    args = parse_args()
    try:
        global PATH_TO_REPO
        PATH_TO_REPO = os.environ["ZETTA_BOX"]
        PATH_TO_REPO += "/" if PATH_TO_REPO[-1] != "/" else ""
    except KeyError:
        sys.stderr.write("Error: please set ZETTA_BOX environment variable\nto path to git repo to store notes in!\n\n")
        return -1

    if not (os.path.exists(PATH_TO_REPO) and os.path.isdir(PATH_TO_REPO)):
        sys.stderr.write("Error: path to repo is invalid!\n\n")
        return -1

        global REPO
    try:
        REPO = Repo(PATH_TO_REPO)
    except InvalidGitRepositoryError:
        sys.stderr.write("Error: path in ZETTA_BOX is a valid path to dir, but there isn't a git repo in it\n\n")
        return -1

    actions = {
        "search": search,
        "edit": edit,
        "create": create,
        "delete": delete,
        "show": show,
        "list": _list,
    }

    if args.action in actions.keys():
        action = actions[args.action]
        if callable(action):
            action(args)


def note_exists(note_id):
    return os.path.exists(note_path_from_id(note_id))


def note_path_from_id(note_id):
    return f"{PATH_TO_REPO}/{note_id}/README.md"


def note_dir_path_from_id(note_id):
    return f"{PATH_TO_REPO}/{note_id}"


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
    note_id = args.id
    if not note_exists(note_id):
        print("\nError: note does not exist!\n\n", file=sys.stderr)
        return
    editor = os.environ.get("EDITOR") if os.environ.get("EDITOR") else "vi"
    path_to_note_file = note_path_from_id(note_id)

    call([editor, path_to_note_file])
    with open(path_to_note_file, "r") as note_file:
        commit_message = note_id + ": " + note_file.readline()

    commit = input("commit? (y/n): ")
    while (commit != "y") and (commit != "n"):
        commit = input("enter either \"y\" or \"n\": ")\

    if (commit == "y"):
        git = REPO.git
        git.add(path_to_note_file)
        try:
            git.commit(m=commit_message)
        except GitCommandError:
            print("Nothing to commit :(\n")


def create(args):
    title = str(args.title)
    editor = os.environ.get("EDITOR") if os.environ.get("EDITOR") else "vi"
    note_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    path_to_note_dir = note_dir_path_from_id(note_id)
    os.mkdir(path_to_note_dir)
    path_to_note_file = note_path_from_id(note_id)
    with open(path_to_note_file, "w") as note_file:
        note_file.write(title)
        note_file.flush()
        call([editor, path_to_note_file])

    with open(path_to_note_file, "r") as note_file:
        commit_message = note_id + ": " + note_file.readline()

    print(commit_message)
    commit = input("commit? (y/n): ")
    while (commit != "y") and (commit != "n"):
        commit = input("enter either \"y\" or \"n\": ")\

    if (commit == "y"):
        git = REPO.git
        git.add(path_to_note_file)
        git.commit(m=commit_message)


def delete(args):
    note_id = args.id
    path_to_note_dir = note_dir_path_from_id(note_id)
    path_to_note_file = note_path_from_id(note_id)
    if note_exists(note_id):
        with open(path_to_note_file, "r") as note_file:
            note_title = note_file.readline()
    else:
        print("\nError: note with given name does not exist :(\n\n", file=sys.stderr)
        return

    do_deletion = input(f"{note_id}: {note_title}\ndelete? (y/n): ")
    if (do_deletion != "y"):
        print("deletion canceled!")
        return

    shutil.rmtree(path_to_note_dir)
    commit_message = "deleted " + note_id
    print(f"deleted {note_id} ({note_title})")
    commit = input("commit? (y/n): ")
    while (commit != "y") and (commit != "n"):
        commit = input("enter either \"y\" or \"n\": ")\

    if (commit == "y"):
        try:
            git = REPO.git
            git.add(path_to_note_file)
            git.commit(m=commit_message)
        except GitCommandError:
            print("\nWarning: could not commit note deletion (was not committed on creation?)\n\n", file=sys.stderr)


def show(args):
    note_id = args.id
    path_to_note_file = note_path_from_id(note_id)
    if note_exists(note_id):
        with open(path_to_note_file, "r") as note_file:
            for line in iter(note_file.readline, ""):
                print(line.rstrip())
    else:
        print("\nError: note with given name does not exist :(\n\n", file=sys.stderr)
        return


def _list(args):
    notes = os.listdir(PATH_TO_REPO)[1:]
    for note_id in notes:
        path_to_note_file = note_path_from_id(note_id)
        with open(path_to_note_file, 'r') as note_file:
            title = note_file.readline()
            if "\n" in title:
                title = title[:-1]
            if "#" in title:
                title = title[1:]

        title = title.strip()
        print(note_id + ": " + title)


if __name__ == "__main__":
    main()
