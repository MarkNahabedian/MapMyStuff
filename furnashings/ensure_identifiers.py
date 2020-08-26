
# Assign unique identifiers to any items that done have one.

import glob
import json
import parse

NEXT_ID = 1

UID_FORMAT = "_x_{uid:04d}"

UNIQUE_ID_FIELD_NAME = "unique_id"

FIELD_PRECEEDING_UNIQUE_ID = "name"

REQUIRED_ITEM_FIELDS = [
  # We exclude width and depth because some items are described by a
  # path, rather than a rectrangle.
  "name", "cssClass", "x", "y"
  ]


def is_item(item):
  for field in REQUIRED_ITEM_FIELDS:
    if not field in item:
      return False
  return True


def main():
  global NEXT_ID
  # Process all json files in the working directory:
  json_files = []
  # Load and scan all JSON files for missing unique_id fields to
  # determine next unused unique id number.
  for filename in glob.glob("*.json"):
    print(filename)
    items = None
    any = False
    with open(filename, "r") as f:
      items = json.load(f)
      for item in items:
        if not is_item(item):
          print("Not an item: %r" % item)
          break
          # continue
        uid = item.get(UNIQUE_ID_FIELD_NAME, "")
        if uid == "":
          any = True
        else:
          # After we've read alll the JSON files, NEXT_ID should be
          # greater than any unique id previously assigned by this
          # program.
          try:
            parsed = parse.parse(UID_FORMAT, uid)
          except Exception as e:
            print("%s: %s" % (e, uid))
            continue
          if parsed:
            this_id = parsed["uid"]
            if this_id >= NEXT_ID:
              NEXT_ID = this_id + 1
    if any:
      json_files.append((filename, items))
    else:
      print("  No empty unique ids")
  print("Next id: %d" % NEXT_ID)
  # Set missing unique ids and rewrite updated JSON files.
  for (filename, items) in json_files:
    count = 0
    for i in range(len(items)):
      item = items[i]
      if not is_item(item):
        continue
      if item.get(UNIQUE_ID_FIELD_NAME, "") == "":
        # unique_id canonically appears right after name.  By
        # inserting it there rather than at the end, as would happen
        # if we just added the field, we avoid creating a diff for the
        # line that would have preceeded it due to the addition of a
        # comma.
        updated_item = {}
        for k, v in item.items():
          if k == FIELD_PRECEEDING_UNIQUE_ID:
            updated_item[k] = v
            updated_item[UNIQUE_ID_FIELD_NAME] = UID_FORMAT.format(uid=NEXT_ID)
            NEXT_ID += 1
            count += 1
          else:
            updated_item[k] = v
        items[i] = updated_item
    with open(filename, "w") as f:
      json.dump(items, f, indent=2)
    print("%d ids assigned in %s" % (count, filename))
          

if __name__ == "__main__":
  main()

