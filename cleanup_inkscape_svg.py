'''
Clean up an SVG file that was written by Inkscape.
'''

import operator
import xml.dom
from xml.dom.minidom import parse
import cssutils      # pip install cssutils
from collections import Counter
from functools import reduce
import svg.path
import re
import numpy


INKSCAPE_OUTPUT_FILE="W31_0-inkscape-output.svg"

SVG_URI = "http://www.w3.org/2000/svg"


def load_inkscape(svg_file):
    return parse(svg_file)


def write_pretty(document, filepath):
    with open(filepath, "w") as f:
        document.writexml(f, addindent="  ", newl="\n")


class AttributeMatcher (object):
    def __init__(self, attrstring):
        split = attrstring.split(":")
        if len(split) == 1:
            self.prefix=""
            self.localName = split[0]
            return
        if len(split) == 2:
            self.prefix=split[0]
            self.localName = split[1]
            return

    def __str__(self):
        if self.prefix == "":
            return self.localNMe
        return "%s.%s" % (self.prefix, self.localName)

    def match(self, attrNode):
        return (attrNode.prefix == self.prefix
                and attrNode.localName == self.localName)


ATTRIBUTES_TO_REMOVE = [
    AttributeMatcher("inkscape:connector-curvature")
    ]


def remove_attributes(element):
    to_delete = []
    for a in element.attributes.values():
        for delete_me in ATTRIBUTES_TO_REMOVE:
            if delete_me.match(a):
                to_delete.append(a)
    for a in to_delete:
        element.removeAttributeNode(a)


def do_elements(node, fun):
    def walk(node):
        if node.nodeType != xml.dom.Node.ELEMENT_NODE:
            return
        fun(node)
        for n in node.childNodes:
            walk(n)
    if node.nodeType == xml.dom.Node.DOCUMENT_NODE:
        walk(node.documentElement)
    else:
        walk(node)


def extract_styles(doc, stylemap={}):
    def es(elt):
        style = elt.getAttribute("style")
        if style == "":
            return
        parsed = cssutils.parseStyle(style)
        key = ';'.join(["%s:%s" % (p.name, p.value)
                        for p in sorted(parsed.getProperties(),
                                        key=lambda x: x.name)])
        if not key in stylemap:
            stylename = "style%d" % len(stylemap)
            stylemap[key] = stylename
            stylemap[stylename] = parsed
        elt.setAttribute("class", stylemap[key])
        elt.removeAttribute("style")
    do_elements(doc, es)
    return stylemap


def add_stylesheet(doc, stylemap):
    '''Updates the stylesheet inkscape_styles (creating it if not present)
    with tyle styles from stylemap.
    '''
    style = ensure_stylesheet(doc, "inkscape_styles")
    classnames = []
    for v in stylemap.values():
        if isinstance(v, str):
            classnames.append(v)
    classnames.sort()
    for c in classnames:
        s = stylemap[c]
        add_srtylesheet_rule(doc, style,
                             "." + c,
                             s.getCssText(" "))


# *** TODO: getElementById isn't finding existing elements, presumably
# because xml.dom doesn't know what the declared ID type attribute is
# because it doesn't have the DTD.
# The SVG namespace URI doesn't point to an XML schema.
def ensure_stylesheet(doc, id):
    '''Ensure that doc has a styleseet with id id and return it.'''
    style = doc.getElementById(id)
    if not style:
        style = new_stylesheet(doc)
        style.setAttribute("ID", id)
    return style


def new_stylesheet(doc):
    style = doc.createElement("style")
    docelt = doc.documentElement
    docelt.insertBefore(style, docelt.firstChild)
    return style


def add_srtylesheet_rule(doc, style, selector, properties):
    style.appendChild(doc.createTextNode("%s\t{ %s; }" %
                                         (selector, properties)))


def svg_line(doc, parent, x0, y0, x1, y1):
    p = doc.createElement("path")
    parent.appendChild(p)
    p.setAttribute("d", "M %d %d L %d %d" % (
        x0, y0, x1, y1))
    return p


def add_grid(doc, spacing, minX, minY, width, height):
    maxX = minX + width - 1
    maxY = minY + height - 1
    grid = doc.createElement("g")
    grid.setAttribute("class", "viewportGrid")
    doc.documentElement.appendChild(grid)
    for x in range(minX, maxX, spacing):
        svg_line(doc, grid, x, minY, x, maxY)
    for y in range(minY, maxY, spacing):
        svg_line(doc, grid, minX, y, maxX, y)
    style = ensure_stylesheet(doc, "decorations")
    add_srtylesheet_rule(doc, style, ".viewportGrid", "stroke: blue")


class Box (object):
    def __init__(self, minX, minY, maxX, maxY):
        self.minX = minX
        self.minY = minY
        self.maxX = maxX
        self.maxY = maxY

    def __str__(self):
        return "x: %d..%d y: %d..%d" % (
            self.minX, self.maxX, self.minY, self.maxY)

    @property
    def width(self):
        return self.maxX - self.minX

    @property
    def height(self):
        return self.maxY - self.minY

    def complex_corners(self):
        '''Returns the four corners of the box and complex number coordinates.'''
        def c(x, y):
            return x + y * 1j
        return [ c(self.minX, self.minY),
                 c(self.maxX, self.minY),
                 c(self.minX, self.maxY),
                 c(self.maxX, self.maxY) ]

    # *** DO WE NEED THIS?
    def within(self, x, y=None):
        if y == None:
            # svg.path uses complex numbers for coordinates.
            y = cPointY(x)
            x = cPointX(x)
        return (self.minx <= x and
                self.maxX >= x and
                self.minY <= y and
                self.maxY >= y)

    def line_intersects(self, svgLine):
        '''Returns True iff any of svgLine is within this Box.'''
        assert isinstance(svgLine, svg.path.Line)
        # The line does not cross the rectangle if all four corners
        # of self are on the same side of svgLine.
        p1 = svgLine.start
        p2 = svgLine.end
        v = cToV(p2 - p1)
        sides = [ numpy.sign(numpy.cross(v, cToV(p - p1))[2])
                  for p in self.complex_corners() ]
        if 4 == abs(reduce(operator.add, sides)):
            # All four corners are on the same side
            return False
        # We need to check the end points of the line
        if cPointX(p1) < self.minX and cPointX(p2) < self.minX:
            return False
        if cPointX(p1) > self.maxX and cPointX(p2) > self.maxX:
            return False
        if cPointY(p1) < self.minY and cPointY(p2) < self.minY:
            return False
        if cPointY(p1) > self.maxY and cPointY(p2) > self.maxY:
            return False
        return True


def test_viewbox(doc, box):
    g = doc.createElement("g")
    g.setAttribute("class", "testViewBoxGroup")
    doc.documentElement.appendChild(g)
    svg_line(doc, g, box.minX, box.minY, box.maxX, box.minY)
    svg_line(doc, g, box.minX, box.maxY, box.maxX, box.maxY)
    svg_line(doc, g, box.minX, box.minY, box.minX, box.maxY)
    svg_line(doc, g, box.maxX, box.minY, box.maxX, box.maxY)
    style = ensure_stylesheet(doc, "decorations")
    add_srtylesheet_rule(doc, style, ".testViewBoxGroup", "stroke: green")


def update_svg_viewbox(doc, box):
    svg = doc.documentElement
    svg.setAttribute(
        "viewBox",
        " ".join([str(x) for x in [box.minX, box.minY, box.width, box.height]]))
    svg.setAttribute("width", "100%")
    svg.removeAttribute("height")


################################################################################
# Clipping SVG paths

def cToV(c):
    '''Represents a complex number as a one dimensional two element numpy array.'''
    return numpy.array([cPointX(c), cPointY(c), 1])


def cPointX(c):
    '''Return the X component of a coordinate represented as a complex number.'''
    return c.real


def cPointY(c):
    '''Return the Y component of a coordinate represented as a complex number.'''
    return c.imag


def clip_paths(doc, box):
    '''Clip all SVG paths to be within the specified bounding box.'''
    for path in doc.getElementsByTagName("path"):
        transform, display = svg_context(path)
        if display:
            parsed_path = svg.path.parse_path(path)
            for step in parsed_path:
                if isinstance(step, svg.path.Line):
                    if not box.line_intersects_box(step):
                        # Ignore step.
                        pass
                else:
                    print("Unsupported path step %r" % step)


def svg_context(path):
    '''Go up the parent chain of path, collecting any transformations 
    and determining if the path is in a context that is displayed.'''
    transform = Transform.identity()
    display = True
    def up(elt):
        '''Accumulate transforms from the inside out.'''
        nonlocal transform
        if elt.nodeType == xml.dom.Node.DOCUMENT_NODE:
            return
        if elt.tagName in ("clipPaths"):
            display = False
        t = elt.getAttribute("transform")
        if t:
            t = parse_transform(t)
            if t:
                # *** Right order?
                transform = t.compose(transform)
        up(elt.parentNode)
    up(path)
    return transform, display


class Transform(object):
    @classmethod
    def identity(cls):
        return cls(numpy.array(
            [[1, 0, 0],
             [0, 1, 0],
             [0, 0, 1]]))

    @classmethod
    def matrix(cls, a, b, c, d, e, f):
        return cls(numpy.array(
            [[a, c, e],
             [b, d, f],
             [0, 0, 1]]))

    def __init__(self, matrix):
        self.matrix = matrix

    def __repr__(self):
        return "Transform(%r)" % self.matrix

    def apply(self, x, y):
        v = self.matrix * [x, y, 1]
        return v[0], v[1]

    def compose(self, other):
        return Transform(self.matrix * other.matrix)


# matrix(0.06,0,0,0.06,7,7)
TRANSFORM_REGEXP = re.compile("(?P<type>[a-zA-Z-_]+)[(](?P<args>[^)]*)[)]")

def parse_transform(transform_string):
    '''Parse an SVG trransform attribute.'''
    # *** Does not yet consider multiple transformations in a single attribute string.
    m = TRANSFORM_REGEXP.match(transform_string)
    if not m:
        return
    if m.group("type") != "matrix":
        return
    t = Transform.matrix(*[float(x.strip()) for x in m.group("args").split(",")])
    return t


################################################################################
# Main

def main():
    doc = load_inkscape(INKSCAPE_OUTPUT_FILE)
    # Get the viewbox
    # *** HACK: viewBox could use different delimiters.  Maybe should use a regular expression.
    viewbox = [ int(x) for x in doc.documentElement.getAttribute("viewBox").split()]
    print("viewBox", viewbox)
    clip_box = Box(700, 450, 970, 610)
    # add_grid(doc, 100, *viewbox)
    # test_viewbox(doc, clip_box)
    clip_paths(doc, clip_box)
    update_svg_viewbox(doc, clip_box)
    # Count elements
    element_counts = Counter()
    def counter(elt):
        element_counts.update([elt.tagName])
    do_elements(doc, counter)
    for item in element_counts.items():
        print("%s\t%d" % item)
    # Get rid of things we don't need
    do_elements(doc, remove_attributes)
    add_stylesheet(doc, extract_styles(doc))
    # Save
    write_pretty(doc, "cleaned_up.svg")


if __name__ == "__main__":
  main()
