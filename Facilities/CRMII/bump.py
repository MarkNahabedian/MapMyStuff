
import argparse
import json

parser = argparse.ArgumentParser(
    prog='bump',
    description='Adjust the x and y properties of the specified items in the specified JSON files')

parser.add_argument(
    "-x",
    action="store",
    dest="x",
    type=int,
    help="Specify an absolute X coordinate for the specified items")

parser.add_argument(
    "-y",
    action="store",
    dest="y",
    type=int,
    help="Specify an absolute Y coordinate for the specified items")

parser.add_argument(
    "-dx",
    action="store",
    dest="dx",
    type=int,
    help="Specify a change for the X coordinate for the specified items")

parser.add_argument(
    "-dy",
    action="store",
    dest="dy",
    type=int,
    help="Specify a change for the Y coordinate for the specified items")

parser.add_argument(
    "-file",
    action="append",
    dest="files",
    help="Specifies a JSON file to modify.  Can be specified multiple times.")

parser.add_argument(
    "items",
    action="store",
    nargs="+",
    help="unique_id of the items to modify")


def move_item(item, args):
    if args.x != None:
        item["x"] = atgs.x
    elif args.dx != None:
        item["x"] += args.dx
        pass
    if args.y != None:
        item["y"] = args.y
    elif args.dy != None:
        item["y"] += args.y
        pass
    pass


def process_file(f, args):
    print("Processing %s" % f)
    with open(f, "r") as io:
        data = json.load(io)
        pass
    for item in data:
        if item["unique_id"] in args.items:
            move_item(item, args)
            pass
        pass
    with open(f, "w") as io:
        json.dump(data, io, indent=4)
        pass
    pass    


def main():
    args = parser.parse_args()
    print(args)
    for f in args.files:
        process_file(f, args)
        pass
    pass

    
if __name__ == '__main__':
    main()

