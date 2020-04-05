'''
Clean up an SVG file that was written by Inkscape.
'''

import sys
import argparse
import operator
import xml.dom
from xml.dom.minidom import parse
import cssutils                        # pip install cssutils
import cssutils.css
from collections import Counter, defaultdict
from functools import reduce
import svg.path
import re
import numpy
import numpy.linalg

# Suppress "WARNING	Property: Unknown Property name" from cssutils.
import logging
cssutils.log.setLevel(logging.CRITICAL)


INKSCAPE_OUTPUT_FILE="W31_0-inkscape-output.svg"

SVG_URI = "http://www.w3.org/2000/svg"


def load_inkscape(svg_file):
    return parse(svg_file)


def write_pretty(document, filepath):
    with open(filepath, "w") as f:
        document.writexml(f, addindent="  ", newl="\n")


class AttributeMatcher (object):
    '''AttributeMatcher provides a way to test if an XML attribute
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


def modify_styles(styles_map):
    for v in styles_map.values():
        if isinstance(v, cssutils.css.CSSStyleDeclaration):
            v.setProperty("vector-effect", "non-scaling-stroke")


def add_stylesheet(doc, stylemap):
    '''Updates the stylesheet inkscape_styles (creating it if not present)
    with styles from stylemap.'''
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
        style.setAttribute("id", id)
        style.setAttribute("type", "text/css")
    return style


def new_stylesheet(doc):
    style = doc.createElement("style")
    docelt = doc.documentElement
    docelt.insertBefore(style, docelt.firstChild)
    return style


cssutils.ser.prefs.omitLastSemicolon = False

def add_stylesheet_rule(doc, style, selector, properties):
    '''Add a CSS rule to the specified style element.  selector and properties are strings.'''
    parsed = (cssutils.parseStyle(properties)
              if isinstance(properties, str)
              else properties)
    rule = cssutils.css.CSSStyleRule(selector, parsed)
    style.appendChild(doc.createTextNode("\n" + rule.cssText))
    return rule


def scope_styles(doc, node, styles_map, modified_properties=""):
    '''Find all of the CSS classes referenced in node or its descendents,
    and create copies of the style rules associated with those classes in
    stylemap into a new stylesheet.  Use the id attribute of node to
    rewstrict those style rules.'''
    classes = set([])
    def collect_class(elt):
        c = elt.getAttribute("class")
        if c:
            classes.add(c)
    do_elements(node, collect_class)
    id = node.getAttribute("id")
    assert id
    stylesheet = ensure_stylesheet(doc, id + "-styles")
    for c in classes:
        add_stylesheet_rule(doc, stylesheet,
                            "#%s .%s" % (id, c),
                            modified_properties + styles_map[c].cssText)


def hide_classes(styles_map, class_names):
    for c in class_names:
        p = styles_map[c]
        assert isinstance(p, cssutils.css.CSSStyleDeclaration)
        p.setProperty("stroke", "#FFF")
        p.setProperty("stroke-opacity", 0)


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
    add_stylesheet_rule(doc, style, ".viewportGrid", "stroke: blue; stroke-width: 1px;")


################################################################################
# ViewBox support


class Box (object):
    def __init__(self, minX, minY, maxX, maxY):
        self.minX = minX
        self.minY = minY
        self.maxX = maxX
        self.maxY = maxY

    def __eq__(self, other):
        return (self.minX == other.minX and
                self.minY == other.minY and
                self.maxX == other.maxX and
                self.maxY == other.maxY)

    def __hash__(self):
        return hash(repr(self))

    def __str__(self):
        return "x: %d..%d y: %d..%d" % (
            self.minX, self.maxX, self.minY, self.maxY)

    def __repr__(self):
        return("Box(%r, %r, %r, %r)" % (
            self.minX,
            self.minY,
            self.maxX,
            self.maxY))

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

    def d(self):
        '''Return an SVG path d attribute value for drawing the box.'''
        return "M %f %f H %f V %f H %f z" % (
            self.minX, self.minY,
            self.maxX,
            self.maxY,
            self.minX)

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


def show_boxes(doc, boxes):
    if not boxes:
        return
    g = doc.createElement("g")
    g.setAttribute("class", "showBox")
    doc.documentElement.appendChild(g)
    for box in boxes:
        path = doc.createElement("path")
        path.setAttribute("class", "box")
        path.setAttribute("d", box.d())
        g.appendChild(path)
        path.appendChild(doc.createComment(repr(box)))
    style = ensure_stylesheet(doc, "decorations")
    add_stylesheet_rule(doc, style, ".showBox",
                        "fill: none; stroke: orange; stroke_width: 2px;")    


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


def update_svg_viewbox(doc, box, increased_height = 0):
    svg = doc.documentElement
    svg.setAttribute(
        "viewBox",
        " ".join([str(x) for x in [box.minX, box.minY, box.width,
                                   box.height + increased_height]]))
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
        if not text_in_box(text, box):
            remove.append(text)
    remove_elements(remove)


def text_in_box(text, box):
    '''Returns True iff text is within box.'''
    # We assume there will only be one.
    # Element counts shows the same number of text and tspan elements.
    ts = text.getElementsByTagName("tspan")
    txt = ts[0] if ts else text
    transform, _ = svg_context(txt)
    # *** I have no idea why but some x and y attributes of tspan
    # elements have multiple values.
    def just_one(s):
        return s.split()[0]
    p = transform.apply(point(float(just_one(txt.getAttribute("x"))),
                              float(just_one(txt.getAttribute("y")))))
    return box.point_within(p)


def clip_paths(doc, box):
    '''Clip all SVG paths to be within the specified bounding box.'''
    remove_paths = []
    for path in doc.getElementsByTagName("path"):
        transform, display = svg_context(path)
        if display:
            parsed_path = svg.path.parse_path(path.getAttribute("d"))
            new_path = svg.path.Path()
            for step in parsed_path:
                # For now just exclude Lines that are wholly outside the Box.
                if isinstance(step, svg.path.Line):
                    if box.line_intersects(transform, step):
                        new_path.append(step)
                elif isinstance(step, svg.path.CubicBezier):
                    # ***** Not clipping cubic bezier for now.
                    new_path.append(step)
                else:
                    new_path.append(step)
                    print("Unsupported path step %r" % step)
            if len(new_path) <= 0:
                remove_paths.append(path)
            else:
                path.setAttribute("d", new_path.d())
    remove_elements(remove_paths)


def svg_context(path, trace_transforms=False):
    '''Go up the parent chain of path, collecting any transformations 
    and determining if the path is in a context that is displayed.'''
    if trace_transforms:
        print("svg_context")
    transform = Transform.identity()
    display = True
    def up(elt):
        '''Accumulate transforms from the inside out.'''
        nonlocal transform, display
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

    @classmethod
    def translate(cls, x, y):
        return cls(numpy.array(
            [[1, 0, x],
             [0, 1, y],
             [0, 0, 1]]))

    def __init__(self, matrix):
        self.matrix = matrix

    def __repr__(self):
        return "Transform(%r)" % self.matrix

    def inverse(self):
        return Transform(numpy.linalg.inv(self.matrix))

    def toSVG(self):
        a = self.matrix[0][0]
        b = self.matrix[1][0]
        c = self.matrix[0][1]
        d = self.matrix[1][1]
        e = self.matrix[0][2]
        f = self.matrix[1][2]
        if (a == 1 and b == 0 and
            c == 0 and d == 1 and
            (list(self.matrix[2]) == [0, 0, 1])):
            return "translate(%f,%f)" % (e, f)
        return "matrix(%f,%f,%f,%f,%f,%f)" % (a, b, c, d, e, f)

    def apply(self, point):
        '''Applies the transform to the point, returning a point that satisfies isPoint.'''
        if isPoint(point):
            return numpy.matmul(self.matrix, point)
        if isinstance(point, complex):
            return self.apply(cToV(point))
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
    if m.group("type") == "matrix":
        return Transform.matrix(*[float(x.strip()) for x in m.group("args").split(",")])
    if m.group("type") == "translate":
        return Transform.translate(*[float(x.strip()) for x in m.group("args").split(",")])
    print("Unsupported transform %s" % transform_string)
    return


################################################################################

def remove_empty_groups(doc):
    '''Remove any g elements that contain nothing but whitespace text.'''
    def empty(node):
        if node.nodeType in (xml.dom.Node.TEXT_NODE,
                             xml.dom.Node.CDATA_SECTION_NODE):
            if len(node.data.strip()) == 0:
                return True
            else:
                return False
        if (node.nodeType == xml.dom.Node.ELEMENT_NODE and
            node.tagName == "g"):
            if len(node.childNodes) > 0:
                return False
            else:
                return True
        return False
    def walk(node):
        # childNodes iteration is compilcated because nodes in the
        # childNodes NodeList might get deleted during the iteration
        # and NodeList iteration doesn';t seem to cope with that.
        i = 0
        previous_node = None
        while i < len(node.childNodes):
            child = node.childNodes.item(i)
            walk(child)
            if node.childNodes.item(i) == child:
                i += 1
        if empty(node):
                node.parentNode.removeChild(node)
    walk(doc.documentElement)


def remove_elements(elements):
    '''Remove each of the XML element nodes in elements from their respective parent nodes.'''
    for r in elements:
        r.parentNode.removeChild(r)


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
# Box purging

def read_box_file(filename):
    '''Reads the box file and returns a list of Box objects.
Each line of the file contains the left X, top Y, right X and bottom Y,
in global coordinates, of a box, delimited by whitespace.'''
    if not filename:
        return []
    boxes = []
    with open(filename, "r") as f:
        for line in f.readlines():
            split = line.split()
            if len(split) != 4:
                print("Wrong number of coordinates in box line: %r"% line)
                continue
            boxes.append(Box(*[float(v) for v in split]))
    return boxes


def tag_boxes(doc, boxes, comment=True):
    '''Tag any SVG paths that are wholly contained within any of boxes by adding an XML comment.
    Returns a dict mapping each Box to a list of the elements that have been tagged for it.'''
    # Tag paths
    map = defaultdict(list)
    for path in doc.getElementsByTagName("path"):
        transform, _ = svg_context(path)
        parsed_path = svg.path.parse_path(path.getAttribute("d"))
        matched_boxes = set([])
        for box in boxes:
            for step in parsed_path:
                if isinstance(step, svg.path.Line):
                    if (box.point_within(transform.apply(step.start)) and
                        box.point_within(transform.apply(step.end))):
                        matched_boxes.add(box)
                        map[box].append(path)
                        continue
                elif isinstance(step, svg.path.CubicBezier):
                    if (box.point_within(transform.apply(step.start)) and
                        box.point_within(transform.apply(step.control1)) and
                        box.point_within(transform.apply(step.control2)) and
                        box.point_within(transform.apply(step.end))):
                        matched_boxes.add(box)
                        map[box].append(path)
                        continue
        if comment and len(matched_boxes) > 0:
            add_tagged_box_comment(doc, path, matched_boxes)
    # Tag text
    for text in doc.getElementsByTagName("text"):
        matched_boxes = []
        for box in boxes:
            if text_in_box(text, box):
                matched_boxes.append(box)
                map[box].append(text)
        if comment and len(matched_boxes) > 0:
            add_tagged_box_comment(doc, text, matched_boxes)
    return map


def add_tagged_box_comment(doc, element, matching_boxes):
    element.appendChild(doc.createComment(
        "  TAGGED BOXES:\n" +
        "\n".join([ repr(box) for box in matching_boxes ]) +
        "\n"))


################################################################################
# Main

parser = argparse.ArgumentParser(
    description='''Cleanup an SVG file that was converted from PDF by Inkscape.''')

parser.add_argument('-input_file', type=str, nargs=None, action='store',
                    default=INKSCAPE_OUTPUT_FILE,
                    help='the input SVG file as written by Inkscape.')

parser.add_argument('-grid_spacing', type=int, nargs=1, action='store',
                    default=0,
                    help='If positive, the spacing of a superimposed reference grid.')

parser.add_argument("-clip_box", type=float, nargs=4, action="store",
                    help="The following four command line arguments specify the left, top, right, and bottom coordinates of the proposed clip box.")

parser.add_argument("-boxes_file", type=str, nargs=None, action="store",
                    help='''A file, each line of which contains four global coordinates describing a box.
Draws an orange box for each one.''')

parser.add_argument("-drawing_scale_box", type=float, nargs=4, action="store",
                    help='''The following four command line arguments specify the left, top, right, and bottom coordinates of the portion of the drawing that shows the drawing's scale.''')

parser.add_argument("-scale_relocation", type=float, nargs=2, action="store",
                    help='''X and Y coordinates for how much to move the drawing scale from its original location.''')

parser.add_argument("-hide_classes", type=str, nargs=None, action="store",
                    default="",
                    help='''Alter the style rules for these CSS classes o that they are invisible.''')

parser.add_argument('-show_clip_box',
                    # action="sture_true",    NOT WORKING
                    action=argparse._StoreTrueAction,
                    help="Show the clip box if one has been specified.")

parser.add_argument("-clip_svg_viewbox",
                    # action="sture_true",    NOT WORKIING
                    action=argparse._StoreTrueAction,
                    help="Set the viewBox SVG attribute to the specified clip box.")

parser.add_argument("-increase_viewbox_height", type=float, nargs=1, action="store",
                    default=[0],
                    help='''Increase SVG viewBox height specified by -clip_svg_viewbox by this amount. ''')

parser.add_argument('-clip',
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


def show_css_class_counts(doc):
    class_counts = Counter()
    def counter(elt):
        class_counts.update([elt.getAttribute("class")])
    do_elements(doc, counter)
    for item in class_counts.items():
        print("%s\t%d" % item)


def main():
    args = parser.parse_args()
    doc = load_inkscape(args.input_file)
    # Count elements
    print("\nBEFORE CHANGES")
    show_element_counts(doc)
    # Extract styles before any document modifications so that class
    # names will be consistent from run to run.
    styles_map = extract_styles(doc)
    # Get the viewbox
    # *** HACK: viewBox could use different delimiters.  Maybe should use a regular expression.
    viewbox = [ int(x) for x in doc.documentElement.getAttribute("viewBox").split()]
    print("viewBox", viewbox)
    clip_box = Box(*args.clip_box) if args.clip_box else None
    print(clip_box)
    boxes_to_show = read_box_file(args.boxes_file)
    # Find the drawing elements that show the drawing's scale and
    # capture the transfomation matrix from each's cuttent SVG context
    scale_elements = [
        (elt, svg_context(elt)[0])
        for elt in tag_boxes(doc, [Box(*args.drawing_scale_box)], False).values().__iter__().__next__()]
    # Remove elements that are outside the clip box.
    if clip_box and args.clip:
        clip_text(doc, clip_box)
        clip_paths(doc, clip_box)
        remove_empty_groups(doc)
        print("\nAFTER CLIPPING")
        show_element_counts(doc)
    if args.clip_svg_viewbox:
        update_svg_viewbox(doc, clip_box, args.increase_viewbox_height[0])
    if args.grid_spacing:
        add_grid(doc, args.grid_spacing[0], *viewbox)
    if clip_box and args.show_clip_box:
        test_viewbox(doc, clip_box)
    # Show and tag the boxes we've been told to.
    box_elements_map = tag_boxes(doc, boxes_to_show)
    show_boxes(doc, boxes_to_show)
    # Relocate the scale elements by putting them into a new SVG group and translating them.
    scale_group = doc.createElement("g")
    doc.documentElement.appendChild(scale_group)
    scale_group.setAttribute("id", "drawingScale")
    for element, transform in scale_elements:
        scale_group.appendChild(element)
        element.setAttribute("transform", transform.toSVG())
    scale_group.setAttribute("transform",
                             Transform.translate(*args.scale_relocation).toSVG())
    # Replicate any style rules referenced by the scale group so that
    # we can modify the style rules of the drawiing proper without
    # affecting the sacale graphics.
    scope_styles(doc, scale_group, styles_map, "vector-effect: none; ")
    # Now that we've copied whatever styles we need for the scale
    # graphics, we can modify the rules of the hide_styles classes and
    # then write that stylesheet.
    hide_classes(styles_map, args.hide_classes.split(","))
    modify_styles(styles_map)
    add_stylesheet(doc, styles_map)
    # Get rid of things we don't need
    do_elements(doc, remove_attributes)
    # Add comments about processing
    # This is done last so that the comment appears before any other
    # added frontmatter line stylesheets.
    if boxes_to_show:
        doc.documentElement.insertBefore(doc.createComment(
            "\nShow boxes:\n%r\n" % boxes_to_show),
        doc.documentElement.firstChild)
    doc.documentElement.insertBefore(doc.createComment(
        '\n' + (' '.join(sys.argv).replace('--', '-') +'\n')),
        doc.documentElement.firstChild)
    # Save
    print("\nAFTER ALL CHANGES")
    show_element_counts(doc)
    print("\nCSS classes:")
    show_css_class_counts(doc)
    write_pretty(doc, "cleaned_up.svg")


if __name__ == "__main__":
  main()
