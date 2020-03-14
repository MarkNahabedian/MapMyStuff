
'''
Clean up an SVG file that was written by Inkscape.
'''


from xml.dom.minidom import parse
import xml.dom as xmldom
# import svg.path


INKSCAPE_OUTPUT_FILE="W31_0-inkscape-output.svg"


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
    for a in element.attributes:
        for delete_me in ATTRIBUTES_TO_REMOVE:
            if delete_me.match(a):
                element.removeAttributeNode(a)


def do_elements(node, fun):
    if node.nodeType != xmldom.Node.ELEMENT_NODE:
        return
    fun(node)
    for n in node.childNodes:
        do_elements(n, fun)


def main():
    doc = load_inkscape(INKSCAPE_OUTPUT_FILE)
    do_elements(doc, remove_attributes)
    write_pretty(doc, "cleaned_up.svg")


if __name__ == "__main__":
  main()
