#!/usr/bin/python3

# A precommit script to test that JSON files are without JSON syntax
# error and only include supported properties.

# To use this pre-commit hook in your local clone of the repository,
# from your repository root do (on unix)
#   ln -s `pwd`/git-hooks/pre-commit.py .git/hooks/pre-commit

import os
import sys
import subprocess
import json

SUPPORTED_PROPERTIES = [
    'name',
    'unique_id',
    'cssClass',
    'clustermarket_id',
    'width',
    'depth',
    'path_d',
    'x',
    'y',
    'rotation',
    'description',
    'description_uri',
    'contents',
    'booking_note',
    'measured'
    ]

# Return a list of properties that appear in a JSON item description
# but are not in SUPPORTED_PROPERTIES.
def check_json_properties(data):
    unknown = []
    for d in data:
        if isinstance(d, dict):
            for property in d:
                if not (property in SUPPORTED_PROPERTIES):
                    if not (property in unknown):
                        unknown.append(property)
    return unknown


def get_files():
     cp = subprocess.run(["git", "diff", "--cached", "--name-only"],
                         capture_output=True,
                         text=True)
     if cp.returncode != 0 or cp.stderr != "":
         raise Exception("git diff failed: %s" % cp.stderr)
         sys.exit(-1)
     return [ s for s in cp.stdout.split("\n") if s ]
     pass


# Return True for failure.
def check_json(filename):
    if os.path.splitext(filename)[1] != ".json":
        return False
    with open(filename, 'r') as file:
        try:
            data = json.load(file)
            unsupported = check_json_properties(data)
            if unsupported:
                print("%s: unsupported properties: %s" % (filename, unsupported))
                return True
        except Exception as e:
            print("%s: %s" % (filename, e))
            return True
            pass
        pass
    return False
    pass


def repo_root():
    f = os.path.dirname(os.path.abspath(__file__))
    while os.path.split(f)[1] in ["hooks", ".git", "git-hooks"]:
        f = os.path.dirname(f)
    return f


def main():
    os.chdir(repo_root())
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = get_files()
    failed = False
    for file in files:
        failed = check_json(file) or failed
    if failed:
        sys.exit(-1)
    sys.exit(0)


if __name__ == "__main__":
    main()

