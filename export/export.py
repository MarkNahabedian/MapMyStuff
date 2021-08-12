# Export the JSON data to a CSV file so they can plan the layout of
# the new shop.

import csv
import json
import os
import os.path


INPUT_DIRECTORY = "furnashings"

OUTPUT_FILE = "everything.csv"

CSV_WRITER_PARAMS = {
    "delimiter": "\t",
    "lineterminator": "\n"
}

class Heading:
    def __init__(self, heading, json=None, convert=lambda x: x):
        self.heading = heading
        self.json = json
        self.convert = convert

    def value(self, json_record):
        if self.json == None:
            return None
        return self.convert(json_record.get(self.json))

def feet_to_inches(feet):
    if feet == None:
        return ""
    return feet * 12

SPREADSHET_HEADINGS = [
    Heading("name", "name"),
    Heading("empty"),
    Heading("id", "unique_id"),
    Heading("width", "width", feet_to_inches),
    Heading("depth", "depth", feet_to_inches)
]

def export_thing(thing, csvwriter):
    row = []
    for cell in SPREADSHET_HEADINGS:
        row.append(cell.value(thing))
    csvwriter.writerow(row)
    pass

def main():
    with open(OUTPUT_FILE, "w") as out:
        writer = csv.writer(out, **CSV_WRITER_PARAMS)
        writer.writerow(
            [heading.heading
             for heading in SPREADSHET_HEADINGS])
        for f in os.listdir(INPUT_DIRECTORY):
            f = os.path.join(INPUT_DIRECTORY, f)
            if not os.path.isfile(f):
                continue
            if os.path.splitext(f)[-1] != ".json":
                continue
            print("exporting %s" % f)
            with open(f, "r") as f:
                for thing in json.load(f):
                    export_thing(thing, writer)
                    pass
            pass
        pass
    pass

if __name__ == '__main__':
    main()

