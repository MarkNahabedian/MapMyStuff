'''
Clean up an SVG file that was written by Inkscape.
'''

import argparse
import numpy
import os.path
import sys
import xml.dom
from collections import Counter, defaultdict
from xml.dom.minidom import parse

import cssutils                        # pip install cssutils
import cssutils.css
import svg.path

# What's the right way to load these?
sys.path.insert(
    0, os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))),
        "lib"))

from box import *
from points import *
from stylesheet import *
from transform import *
from xml_utils import *


# Suppress "WARNING	Property: Unknown Property name" from cssutils.
import logging
cssutils.log.setLevel(logging.CRITICAL)


INKSCAPE_OUTPUT_FILE="W31_0-inkscape-output.svg"

SVG_URI = "http://www.w3.org/2000/svg"


def load_inkscape(svg_file):
    return parse(svg_file)


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
        p = styles_map.get(c, None)
        if p == None:
            continue
        assert isinstance(p, cssutils.css.CSSStyleDeclaration)
        p.setProperty("stroke", "none")
        p.setProperty("fill", "none")
        p.setProperty("stroke-opacity", 0)


def thing_styles(doc):
    stylesheet = ensure_stylesheet(doc, "thing-styles") 
    stylesheet.appendChild(doc.createCDATASection(
        "\n@import url(../furnashings/thing_styles.css);\n"))


################################################################################
# Grid


def svg_line(doc, parent, x0, y0, x1, y1):
    p = doc.createElement("path")
    parent.appendChild(p)
    p.setAttribute("d", "M %d %d L %d %d" % (
        x0, y0, x1, y1))
    return p


def add_grid(doc, spacing, box):
    print("GRID BOX", box)
    grid = doc.createElement("g")
    grid.setAttribute("class", "viewportGrid")
    doc.documentElement.appendChild(grid)
    # Draw X coordinates from right tyo left.
    grid.appendChild(doc.createComment("Vertical rules"))
    x = box.maxX
    while x >= box.minX:
        svg_line(doc, grid, x, box.minY, x, box.maxY)
        x -= spacing
    # Y coordinates from top to bottom.
    grid.appendChild(doc.createComment("horizontal rules"))
    y = box.minY
    while y <= box.maxY:
        svg_line(doc, grid, box.minX, y, box.maxX, y)
        y += spacing
    style = ensure_stylesheet(doc, "decorations")
    add_stylesheet_rule(
        doc, style,
        ".viewportGrid", "stroke: yellow; stroke-width: 1px; stroke-opacity: 0.5;")


def add_real_world_group(doc, grid_spacing, grid_real_world_size, box):
    '''Add an SVG group to doc whose coordinate system origin is at the 
    top right of the clip grid with positive X pointing left and positive
    Y pointing down, and scaled so that the spacing between grid lines
    represents grid_real_world_size real world units.'''
    real_world = doc.createElement("g")
    doc.documentElement.appendChild(real_world)
    real_world.setAttribute("id", "real-world")
    scale = grid_spacing / grid_real_world_size
    real_world.setAttribute(
        "transform",
        Transform.translate(box.maxX, box.minY).toSVG() + " " +
        Transform.scale(-scale, scale).toSVG())


################################################################################
# ViewBox support
        

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
    # That was true of Inkscape's output, the output from Acrobat has
    # no tspan elements.
    ts = text.getElementsByTagName("tspan")
    if ts:
        txt = ts[0]
    else:
        txt = text
    transform, _ = svg_context(txt)
    # *** I have no idea why but some x and y attributes of tspan
    # elements have multiple values.
    def just_one(s):
        if s:
            return s[0]
        else:
            return 0
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
                    if box.cubicBezier_intersects(transform, step):
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
            t = Transform.parseSVG(t)
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
    c.setAttribute("style", "fill:blue; stroke:none; stroke-width:2; stroke-opacity:0.5")
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
    c.setAttribute("style", "fill:none; stroke:red; stroke-width:2; stroke-opacity:0.5")
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

parser.add_argument('-grid_spacing', type=float, nargs=1, action='store',
                    help='If positive, the spacing of a superimposed reference grid.')

parser.add_argument("-grid_real_world_size", type=float, nargs=1, action="store",
                    help='''How many real world units (e.g. feet) a single grid line represents.''')

parser.add_argument("-clip_box", type=float, nargs=4, action="store",
                    help="The following four command line arguments specify the left, top, right, and bottom coordinates of the proposed clip box. Defaults to the viewBox of the outer SVG element.")

parser.add_argument("-boxes_file", type=str, nargs=None, action="store",
                    help='''A file, each line of which contains four global coordinates describing a box.
Draws an orange box for each one.''')

parser.add_argument("-drawing_scale_box", type=float, nargs=4, action="store",
                    help='''The following four command line arguments specify the left, top, right, and bottom coordinates of the portion of the drawing that shows the drawing's scale.''')

parser.add_argument("-scale_relocation", type=float, nargs=2, action="store",
                    help='''X and Y coordinates for how much to move the drawing scale from its original location.''')

parser.add_argument("-hide_classes", type=str, nargs=None, action="store",
                    default="",
                    help='''Alter the style rules for these CSS classes so that they are invisible.''')

parser.add_argument('-show_clip_box',
                    action="store_true",
                    help="Show the clip box if one has been specified.")

parser.add_argument("-clip_svg_viewbox",
                    action="store_true",
                    help="Set the viewBox SVG attribute to the specified clip box.")

parser.add_argument("-increase_viewbox_height", type=float, nargs=1, action="store",
                    default=[0],
                    help='''Increase SVG viewBox height specified by -clip_svg_viewbox by this amount. ''')

parser.add_argument('-clip',
                    action="store_true",
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
    clip_box = Box(*args.clip_box) if args.clip_box else Box.xywh(*viewbox)
    print(clip_box)
    boxes_to_show = read_box_file(args.boxes_file)
    # Find the drawing elements that show the drawing's scale and
    # capture the transfomation matrix from each's current SVG context
    scale_elements = [
        (elt, svg_context(elt)[0])
        for elt in ([] if args.drawing_scale_box == None
                    else tag_boxes(doc, [Box(*args.drawing_scale_box)], False).values())]
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
        print(viewbox)
        # If we're shrinking the SVG viewBox to the useful part of the
        # floor plan then alighn the grid to the top right corner,
        # otherwise to the global coordinate system.
        add_grid(doc, args.grid_spacing[0],
                 clip_box if args.clip_svg_viewbox
                 else Box.xywh(*viewbox))
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
    if args.scale_relocation != None:
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
    if args.grid_real_world_size:
        add_real_world_group(doc,
                             args.grid_spacing[0],
                             args.grid_real_world_size[0],
                             clip_box)
    # Thing styles
    // thing_styles(doc)
    # Add comments about processing
    # This is done last so that the comment appears before any other
    # added frontmatter like stylesheets.
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
