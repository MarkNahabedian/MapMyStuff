#!"C:/Users/Mark Nahabedian/AppData/Local/Programs/Python/Python39/python.exe"

# The JavaScript console in Chrome gives a crappy location for JSOn
# syntax errors.

# Maybe python will do better.

import json
import os
import os.path


def main():
    for f in os.listdir("."):
        if not os.path.isfile(os.path.abspath(f)):
            continue
        if f.split(".")[-1] != "json":
            continue
        with open(f, "r") as input:
            try:
                json.load(input)
            except json.decoder.JSONDecodeError as e:
                print("%s: %s\n" %(f, e))
                pass
            pass
        pass
    pass


if __name__ == "__main__":
    main()
