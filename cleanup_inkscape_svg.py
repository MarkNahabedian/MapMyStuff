'''
Clean up an SVG file that was written by Inkscape.
'''


from xml.dom.minidom import parse
import xml.dom
import cssutils      # pip install cssutils
from collections import Counter
# import svg.path


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


def add_grid(doc, minX, minY, width, height):
    maxX = minX + width - 1
    maxY = minY + height - 1
    grid = doc.createElement("g")
    grid.setAttribute("class", "viewportGrid")
    doc.documentElement.appendChild(grid)
    for x in range(minX, maxX, 100):
        svg_line(doc, grid, x, minY, x, maxY)
    for y in range(minY, maxY, 100):
        svg_line(doc, grid, minX, y, maxX, y)
    style = ensure_stylesheet(doc, "decorations")
    add_srtylesheet_rule(doc, style, ".viewportGrid", "stroke: blue")


def test_viewbox(doc, minX, minY, maxX, maxY):
    box = doc.createElement("g")
    box.setAttribute("class", "testViewBox")
    doc.documentElement.appendChild(box)
    svg_line(doc, box, minX, minY, maxX, minY)
    svg_line(doc, box, minX, maxY, maxX, maxY)
    svg_line(doc, box, minX, minY, minX, maxY)
    svg_line(doc, box, maxX, minY, maxX, maxY)
    style = ensure_stylesheet(doc, "decorations")
    add_srtylesheet_rule(doc, style, ".testViewBox", "stroke: green")


def main():
    doc = load_inkscape(INKSCAPE_OUTPUT_FILE)
    # Get the viewbox
    # *** HACK: viewBox could use different delimiters.  Maybe should use a regular expression.
    viewbox = [ int(x) for x in doc.documentElement.getAttribute("viewBox").split()]
    print("viewBox", viewbox)
    add_grid(doc, *viewbox)
    test_viewbox(doc, 700, 450, 970, 610)
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
