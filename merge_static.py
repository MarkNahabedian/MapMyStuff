# This script merges a template HTML file (floor_plan.html), the
# cleaned up SVG file (floor_plan_cleanup/cleaned_up.svg), javascript
# code to place things onto the floor plan (placement.js) and the data
# file (furnashings/things.json) into a single HTML file which shows
# and lists the things.

# This script is made obsolete by a working version of placement.js.

import json
import os.path
import sys
import xml.dom
import xml.dom.minidom
import cssutils                        # pip install cssutils
import cssutils.css

# What's the right way to load these?
sys.path.insert(
    0, os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "lib"))

from transform import *
from xml_utils import *
from stylesheet import *


# Input files:
HTML_TEMPLATE = "floor_plan.html"
JAVASCRIPT = "placement.js"
FLOOR_PLAN = "floor_plan_cleanup/cleaned_up.svg"
THINGS = "furnashings/things.json"

#Output file
OUTPUT = "merged_floor_plan.html"
  

THING_STYLES= '''
.thing {
  stroke: red;
  fill: lightgray;
  stroke-width: 1;
  vector-effect: non-scaling-stroke;
}
'''

def merge_svg(doc):
  svgdoc = xml.dom.minidom.parse(FLOOR_PLAN)
  for object in doc.getElementsByTagName("object"):
    if object.getAttribute("data") == "floor_plan.svg":
      object.parentNode.insertBefore(svgdoc.documentElement, object)
      object.parentNode.removeChild(object)
      break


def merge_javascript(doc):
  with open(JAVASCRIPT, "r") as f:
    js = f.read()
  with open(THINGS, "r") as f:
    things = f.read()
  for script in doc.getElementsByTagName("script"):
    if script.getAttribute("src") == "placement.js":
      script.removeAttribute("src");
      script.appendChild(doc.createTextNode("//"))
      script.appendChild(doc.createCDATASection(
          "\nTHINGS = " + things + ";\n\n" + js + "\n//"))
      break


def main():
  doc = xml.dom.minidom.parse(HTML_TEMPLATE)
  merge_svg(doc)
  merge_javascript(doc)
  ensure_stylesheet(doc, "thing-styles").appendChild(doc.createTextNode(THING_STYLES))
  write_pretty(doc, OUTPUT)
    

if __name__ == "__main__":
  main()


