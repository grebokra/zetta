#!/usr/bin/env python3
import os
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="A Tool for managing a \"box of notes\"")
    subparsers = parser.add_subparsers(dest="action")
    
    search_parser = subparsers.add_parser("search",
            help="search through notes")
    search_parser.add_argument("pattern",
            help="pattern to search in notes for")

    edit_parser = subparsers.add_parser("edit",
            help="edit note by id")
    edit_parser.add_argument("id",
            help="note id")
    
    create_parser = subparsers.add_parser("create",
            help="create new note")
    
    delete_parser = subparsers.add_parser("delete",
            help="delete note by id")
    delete_parser.add_argument("id",
            help="note id")

    args = parser.parse_args()
    
    try:
        path_to_repo = os.environ["ZETTA_BOX"]
    except KeyError as e:
        exit(-1)

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
    pass

def edit(args):
    pass

def create(args):
    pass

def delete(args):
    pass

if __name__ == "__main__":
    exit(main())
