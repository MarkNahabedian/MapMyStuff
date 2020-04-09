# Some utilities for dealing with XML files.


import xml.dom


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


def write_pretty(document, filepath):
    '''Format the XML document to filepath.'''
    with open(filepath, "w") as f:
        document.writexml(f, addindent="  ", newl="\n")


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

