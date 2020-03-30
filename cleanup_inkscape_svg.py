'''
Clean up an SVG file that was written by Inkscape.
'''

import sys
import argparse
import operator
import xml.dom
from xml.dom.minidom import parse
import cssutils      # pip install cssutils
from collections import Counter
from functools import reduce
import svg.path
import re
import numpy
import numpy.linalg


INKSCAPE_OUTPUT_FILE="W31_0-inkscape-output.svg"

SVG_URI = "http://www.w3.org/2000/svg"


def load_inkscape(svg_file):
    return parse(svg_file)


def write_pretty(document, filepath):
    with open(filepath, "w") as f:
        document.writexml(f, addindent="  ", newl="\n")


class AttributeMatcher (object):
    '''AttributeMatcher provide a way to test if an XML attribute
    node's qualified name matches the name specified.'''
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


def getElementById(doc, id):
    '''The getDocumentById methods in xml.dom depend on having a
    document schema that identifies an ID attribute..  This function
    is a workaround for that.'''
    found = []
    def f(node):
        eid = node.getAttribute("id")
        if eid and eid == id:
            found.append(node)
    do_elements(doc.documentElement, f)
    if len(found) == 1:
        return found[0]
    return None


################################################################################
# Stylesheet manipulation


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
        add_stylesheet_rule(doc, style,
                            "." + c,
                            s.getCssText(" "))


# *** TODO: getElementById isn't finding existing elements, presumably
# because xml.dom doesn't know what the declared ID type attribute is
# because it doesn't have the DTD.
# The SVG namespace URI doesn't point to an XML schema.
def ensure_stylesheet(doc, id):
    '''Ensure that doc has a styleseet with id id and return it.'''
    # style = doc.getElementById(id)
    style = getElementById(doc, id)
    if not style:
        style = new_stylesheet(doc)
        style.setAttribute("ID", id)
    return style


def new_stylesheet(doc):
    style = doc.createElement("style")
    docelt = doc.documentElement
    docelt.insertBefore(style, docelt.firstChild)
    return style


def add_stylesheet_rule(doc, style, selector, properties):
    style.appendChild(doc.createTextNode("%s\t{ %s; }" %
                                         (selector, properties)))


################################################################################
# Grid


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
    add_stylesheet_rule(doc, style, ".viewportGrid", "stroke: blue")


################################################################################
# ViewBox support


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

    def corners(self):
        '''Returns the four corners of the box as points (satisfying isPoint).'''
        return [ point(self.minX, self.minY),
                 point(self.maxX, self.minY),
                 point(self.minX, self.maxY),
                 point(self.maxX, self.maxY) ]

    def point_within(self, point):
        assert isPoint(point)
        x = point[0]
        y = point[1]
        return (self.minX <= x and
                self.maxX >= x and
                self.minY <= y and
                self.maxY >= y)

    def line_intersects(self, transform, svgLine):
        '''Returns True iff any of svgLine is within this Box.'''
        assert isinstance(svgLine, svg.path.Line)
        # The line does not cross the rectangle if all four corners
        # of self are on the same side of svgLine.
        p1 = transform.apply(cToV(svgLine.start))
        p2 = transform.apply(cToV(svgLine.end))
        v = p2 - p1
        sides = [ numpy.sign(numpy.cross(v, p - p1)[2])
                  for p in self.corners() ]
        if 4 == abs(reduce(operator.add, sides)):
            # All four corners are on the same side
            return False
        # We need to check the end points of the line
        def x(p): return p[0]
        def y(p): return p[1]
        if x(p1) < self.minX and x(p2) < self.minX:
            return False
        if x(p1) > self.maxX and x(p2) > self.maxX:
            return False
        if y(p1) < self.minY and y(p2) < self.minY:
            return False
        if y(p1) > self.maxY and y(p2) > self.maxY:
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
    add_stylesheet_rule(doc, style, ".testViewBoxGroup", "stroke: green")


def update_svg_viewbox(doc, box):
    svg = doc.documentElement
    svg.setAttribute(
        "viewBox",
        " ".join([str(x) for x in [box.minX, box.minY, box.width, box.height]]))
    svg.setAttribute("width", "100%")
    svg.removeAttribute("height")


################################################################################
# Clipping SVG paths

def point(x, y):
    "Constructs a point suitable for numpy arithmetic."
    return numpy.array([x, y, 1])


def isPoint(p):
    return (isinstance(p, numpy.ndarray) and
            p.shape == (3,))


def cToV(c):
    '''Represents a complex number as a one dimensional two element numpy array.'''
    return point(cPointX(c), cPointY(c))


def cPointX(c):
    '''Return the X component of a coordinate represented as a complex number.'''
    return c.real


def cPointY(c):
    '''Return the Y component of a coordinate represented as a complex number.'''
    return c.imag


def clip_text(doc, box):
    remove = []
    for text in doc.getElementsByTagName("text"):
        # We assume there will only be one.
        # Element counts shows the same number of text and tspan elements.
        ts = text.getElementsByTagName("tspan")
        txt = ts[0] if ts else text
        transform, display = svg_context(txt)
        if not display:
            continue
        # *** I have no idea why but some x and y attributes of tspan
        # elements have multiple values.
        def just_one(s):
            return s.split()[0]
        p = transform.apply(point(float(just_one(txt.getAttribute("x"))),
                                  float(just_one(txt.getAttribute("y")))))
        if not box.point_within(p):
            remove.append(text)
    for text in remove:
        text.parentNode.removeChild(text)


def clip_paths(doc, box):
    '''Clip all SVG paths to be within the specified bounding box.'''
    remove_paths = []
    for path in doc.getElementsByTagName("path"):
        transform, display = svg_context(path)
        if display:
            parsed_path = svg.path.parse_path(path.getAttribute("d"))
            new_path = svg.path.Path()
            for step in parsed_path:
                # For now just excluded Lines that are wholly outside the Box.
                if isinstance(step, svg.path.Line):
                    if box.line_intersects(transform, step):
                        new_path.append(step)
                elif isinstance(step, svg.path.CubicBezier):
                    pass    # ***** IGNORING CubicBezier
                else:
                    new_path.append(step)
                    print("Unsupported path step %r" % step)
            if len(new_path) <= 0:
                remove_paths.append(path)
            else:
                path.setAttribute("d", new_path.d())
    for path in remove_paths:
        path.parentNode.removeChild(path)


def svg_context(path, trace_transforms=False):
    '''Go up the parent chain of path, collecting any transformations 
    and determining if the path is in a context that is displayed.'''
    if trace_transforms:
        print("svg_context")
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
                if trace_transforms:
                    print(t)
                # See https://www.w3.org/TR/2010/WD-SVG11-20100622/coords.html, 7.5 Nested Transformations
                # It says that as you descend the SVG tree, an inner
                # transformation is post-multiplied to the outer
                # transformation.
                # Here we are ascending the tree from the inside out,
                # so the outer matrix is premultiplied with the inner
                # matrix.
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

    def inverse(self):
        return Transform(numpy.linalg.inv(self.matrix))

    def apply(self, point):
        if isPoint(point):
            return numpy.matmul(self.matrix, point)
        if isinstance(cpoint, complex):
            result = self.apply(cToV(cpoint))
            return result[0] + result[1] ^ 1j
        assert False, "Unsupported point type: %r" % point

    def compose(self, other):
        return Transform(numpy.matmul(self.matrix, other.matrix))


# matrix(0.06,0,0,0.06,7,7)
TRANSFORM_REGEXP = re.compile("(?P<type>[a-zA-Z-_]+)[(](?P<args>[^)]*)[)]")

def parse_transform(transform_string):
    '''Parse an SVG trransform attribute.  Returns a Transform.'''
    # *** Does not yet consider multiple transformations in a single attribute string.
    m = TRANSFORM_REGEXP.match(transform_string)
    if not m:
        return
    if m.group("type") != "matrix":
        print("Unsupported transform %s" % trransform_string)
        return
    t = Transform.matrix(*[float(x.strip()) for x in m.group("args").split(",")])
    return t


################################################################################

def add_test_lines(doc, context, cx, cy, delta):
    '''Draw a square spiral centered at cx, cy to provide lines to test clipping.'''
    assert context.nodeType == xml.dom.Node.ELEMENT_NODE, repr(context)
    transform, _ = svg_context(context)
    xy = cx + cy * 1j
    print("add_test_lines centered at %r\n%r %d %d" % (
        transform.apply(point(cx, cy)),
        transform.matrix,
        cx, cy))
    path = svg.path.Path()
    deltas = (1, 1j, -1, -1j)
    def path_end():
        if len(path) == 0:
            return xy
        return path[-1].end
    for count in range(1, 20):
        path.append(svg.path.Line(path_end(), xy + count * delta * deltas[count % 4]))
    g = doc.createElement("g")
    g.setAttribute("class", "testPaths")
    g.setAttribute("style", "fill:none;stroke:orange;stroke-width:5;")
    context.appendChild(g)
    p = doc.createElement("path")
    p.setAttribute("d", path.d())
    g.appendChild(p)


def locator_circle(doc, parent, x, y, radius):
    c = g = doc.createElement("circle")
    c.setAttribute("cx", "%d" % x)
    c.setAttribute("cy", "%d" % y)
    c.setAttribute("r", "%d" % radius)
    c.setAttribute("style", "fill:blue; stroke:none; stroke-width:2; opacity:0.5")
    parent.appendChild(c)
    transform, _ = svg_context(parent, trace_transforms=True)
    # transform = transform.inverse()
    center = transform.apply(point(x, y))
    print("locator_circle centered at %r\n%r %d %d" % (
        center,
        transform.matrix,
        x, y))
    c = g = doc.createElement("circle")
    c.setAttribute("cx", "%d" %  center[0])
    c.setAttribute("cy", "%d" % center[1])
    c.setAttribute("r", "%d" % 20)
    c.setAttribute("style", "fill:none; stroke:red; stroke-width:2; opacity:0.5")
    doc.documentElement.appendChild(c)


################################################################################
# Main

parser = argparse.ArgumentParser(
    description='''Cleanup an SVG file that was converted from PDF by Inkscape. ''')

parser.add_argument('--input_file', type=str, nargs=None, action='store',
                    default=INKSCAPE_OUTPUT_FILE,
                    help='the input SVG file as written by Inkscape.')

parser.add_argument('--grid_spacing', type=int, nargs=1, action='store',
                    default=0,
                    help='If positive, the spacing of a superimposed reference grid.')

parser.add_argument("--clip_box", type=float, nargs=4, action="store",
                    help="The following four command line arguments specify the left, top, right, and bottom coordinates of the proposed clip box.")

parser.add_argument('--show_clip_box',
                    # action="sture_true",    NOT WORKING
                    action=argparse._StoreTrueAction,
                    help="Show the clip box if one has been specified.")

parser.add_argument("--clip_svg_viewbox",
                    # action="sture_true",    NOT WORKIING
                    action=argparse._StoreTrueAction,
                    help="Set the viewBox SVG attribute to the specified clip box.")

parser.add_argument('--clip',
                    # action="sture_true",    NOT WORKING
                    action=argparse._StoreTrueAction,
                    help="Clip SVG paths to within the clip box.")


def show_element_counts(doc):
    element_counts = Counter()
    def counter(elt):
        element_counts.update([elt.tagName])
    do_elements(doc, counter)
    for item in element_counts.items():
        print("%s\t%d" % item)


def main():
    args = parser.parse_args()
    doc = load_inkscape(args.input_file)
    # Count elements
    print("\nBEFORE CHANGES")
    show_element_counts(doc)
    # Extract styles before any document modifications so that class
    # names will be consistent from run to run.
    add_stylesheet(doc, extract_styles(doc))
    # Get the viewbox
    # *** HACK: viewBox could use different delimiters.  Maybe should use a regular expression.
    viewbox = [ int(x) for x in doc.documentElement.getAttribute("viewBox").split()]
    print("viewBox", viewbox)
    clip_box = Box(*args.clip_box) if args.clip_box else None
    print(clip_box)
    ############################################################
    # Add Sone lines to test clipping.
    # add_test_lines(doc, doc.documentElement, 750, 500, 10)
    # add_test_lines(doc, doc.getElementById("g22358"),
    #                9300, 7000, 10)
    # add_test_lines(doc, getElementById(doc, "g22358"),
    #                9300, 7000, 10)  # 6697,5740
    locator_circle(doc, getElementById(doc, "g22832"),
                   0.00858, -89, 100)
    ############################################################
    if clip_box and args.clip:
        clip_text(doc, clip_box)
        clip_paths(doc, clip_box)
        print("\nAFTER CLIPPING")
        show_element_counts(doc)
    if args.clip_svg_viewbox:
        update_svg_viewbox(doc, clip_box)
    if args.grid_spacing:
        add_grid(doc, args.grid_spacing[0], *viewbox)
    if clip_box and args.show_clip_box:
        test_viewbox(doc, clip_box)
    # Get rid of things we don't need
    do_elements(doc, remove_attributes)
    # Add a comment about processing
    # This is done last so that the comment appears before any other
    # added frontmatter line stylesheets.
    doc.documentElement.insertBefore(doc.createComment(
        '\n' + (' '.join(sys.argv).replace('--', '-') +'\n')),
        doc.documentElement.firstChild)
    # Save
    print("\nAFTER ALL CHANGES")
    show_element_counts(doc)
    write_pretty(doc, "cleaned_up.svg")


if __name__ == "__main__":
  main()
