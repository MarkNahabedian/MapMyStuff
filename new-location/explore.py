#!"C:/Users/Mark Nahabedian/AppData/Local/Programs/Python/Python39/python.exe"

# The SVG drawing that Coby Unger sent is pleasently simple, with only
# one CSS class and only line elements.
#
# I may =need to remove some spurious text, but mostly I need to
# identify the scale.

import argparse
import math
import xml.dom
from xml.dom.minidom import parse
from collections import Counter
import svg.path
import numpy


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

class Line:
    def __init__(self, elt):
        assert elt.nodeType == xml.dom.Node.ELEMENT_NODE
        assert elt.tagName == "line"
        x1 = float(elt.getAttribute("x1"))
        x2 = float(elt.getAttribute("x2"))
        y1 = float(elt.getAttribute("y1"))
        y2 = float(elt.getAttribute("y2"))
        self.center = ((x1 + x2)/2, (y1 + y2)/2)
        self.length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        d1 = math.sqrt(x1**2 + y1**2)
        d2 = math.sqrt(x2**2 + y2**2)
        if d1 > d2:
            self.start = (x2, y2)
            self.end = (x1, y1)
        else:
            self.start = (x1, y1)
            self.end = (x2, y2)

    def __str__(self):
        return "Line %f %s-%s" % (
            self.length,
            self.start,
            self.end
            )
pass

def make_lines(doc):
    lines = []
    def line(elt):
        if elt.nodeType == xml.dom.Node.ELEMENT_NODE and elt.tagName == "line":
            lines.append(Line(elt))
    do_elements(doc, line)
    return lines
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
    lines = make_lines(doc)
    counts, buckets = numpy.histogram([line.length for line in lines],
                                      bins=(0,10, 100, 1000))
    for i in range(0, len(counts)):
        print("  {:6d}  {:8.2f}  {:6d}".format(buckets[i], counts[i], buckets[i+1]))

    longest = lines[0]
    shortest = lines[0]
    for line in lines:
        if line.length > longest.length:
            longest = line
        if line.length < shortest.length:
            shortest = line
    print("shortest: ", shortest, "\nlongest: ", longest)


if __name__ == "__main__":
  main()
