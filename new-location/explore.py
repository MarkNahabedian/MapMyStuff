#!"C:/Users/Mark Nahabedian/AppData/Local/Programs/Python/Python39/python.exe"

# The SVG drawing that Coby Unger sent is pleasently simple, with only
# one CSS class and only line elements.
#
# I may =need to remove some spurious text, but mostly I need to
# identify the scale.

import argparse
import xml.dom
from xml.dom.minidom import parse
from collections import Counter
import svg.path


def do_elements(e, f):
    f(e)
    for n in e.childNodes:
        do_elements(n, f)
    pass
pass

def show_element_counts(doc):
    element_counts = Counter()
    def counter(elt):
        if elt.nodeType == xml.dom.Node.ELEMENT_NODE:
            element_counts.update([elt.tagName])
    do_elements(doc, counter)
    for item in element_counts.items():
        print("%s\t%d" % item)
    pass
pass


################################################################################

parser = argparse.ArgumentParser(
    description='''Explore the SVG file of the new Hobby Shop space.''')

parser.add_argument('-input_file', type=str, nargs=None, action='store',
                    default="c:/Users/Mark Nahabedian/HobbyShop/new-location/new_space_2021-09-16.svg",
                    help='the input SVG file as written by Inkscape.')

def main():
    args = parser.parse_args()
    doc = parse(args.input_file)
    show_element_counts(doc)
    # Collect distribution of line lengths and angles
    pass


if __name__ == "__main__":
  main()
