# This script places the things described in furnashings/things.json
# onto floor_plan_cleanup/cleaned_up.svg to produce a static
# floor_plan.svg file.  This is an interim measure until I can get
# things running as a web service.

# Now that placement.js is working, this script is no longer needed.

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


INPUT = "floor_plan_cleanup/cleaned_up.svg"
OUTPUT = "floor_plan.svg"
THINGS = "furnashings/things.json"

THING_STYLES= '''
.thing {
  stroke: red;
  fill: lightgray;
  stroke-width: 1;
  vector-effect: non-scaling-stroke;
}
'''


def main():
  doc = xml.dom.minidom.parse(INPUT)
  real_world = getElementById(doc, "real-world")
  stylesheet = ensure_stylesheet(doc, "thing-styles")
  stylesheet.appendChild(doc.createTextNode(THING_STYLES))
  with open(THINGS, "r") as f:
    things = json.load(f)
  for thing in things:
    print(thing["name"])
    rect = doc.createElement("rect")
    real_world.appendChild(rect)
    title = doc.createElement("title")
    title.appendChild(doc.createTextNode(thing["name"]))
    rect.appendChild(title)
    rect.setAttribute("class", thing["cssClass"])
    rect.setAttribute("width", str(thing["width"]))
    rect.setAttribute("height", str(thing["depth"]))
    rect.setAttribute("x", str(- thing["width"] / 2))
    rect.setAttribute("y", str(- thing["depth"] / 2))
    rect.setAttribute("transform",
                      Transform.rotate(thing["rotation"]).toSVG() + " " +
                      Transform.translate(thing["x"], thing["y"]).toSVG())
  write_pretty(doc, OUTPUT)
    

if __name__ == "__main__":
  main()


