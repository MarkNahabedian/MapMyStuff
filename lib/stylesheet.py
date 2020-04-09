# Common functions for working with stylesheets.


import cssutils

from xml_utils import *


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

