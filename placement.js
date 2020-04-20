// Place things onto the floorplan.

function load_and_draw_things() {
  console.log("load_and_draw_things");
  fetch_things("furnashings/things.json");
}

function fetch_things(path) {
  console.log("fetch_things " + path);
  fetch(path).then(function(response) {
    if (!response.ok) {
      console.log(response.statusText);
      return;
    }
    response.text().then(
      function(txt) {
        var things = JSON.parse(txt);
        for(var i = 0; i < things.lengtrh; i++) {
          ALL_THINGS.push(things[i]);
        }
        draw_things(things, path);
      },
      console.log);
  });
}

function draw_things(things, from_path) {
  console.log('draw_things from ', from_path);
  var svgdoc = document.getElementById("floor_plan_svg").contentDocument;
  var g = svgdoc.getElementById("real-world");
  // Adding this click handler breaks the click to describe behavior.
  // g.onclick = enptySpaceClicked;
  var index = 0;
  while (index < things.length) {
    var thing = things[index];
    thing["from_file"] = from_path;
    thing["unique_id"] = item_unique_id_counter++;
    ALL_THINGS.push(things[index]);
    draw_thing(svgdoc, g, thing, index);
    index += 1;
  }
}

function draw_thing(svgdoc, g, thing, index) {
  console.log("draw_thing " + thing.name);
  var rect = svgdoc.createElementNS(g.namespaceURI, "rect");
  var title = svgdoc.createElementNS(g.namespaceURI, "title");
  title.textContent = thing.name;
  rect.setAttribute("class", thing.cssClass);
  rect.setAttribute("id", thing_svg_id(thing));
  rect.setAttribute("x", thing.x);
  rect.setAttribute("y", thing.y);
  rect.setAttribute("width", thing.width);
  rect.setAttribute("height", thing.depth);
  rect.setAttribute("x", - thing.width / 2);
  rect.setAttribute("y", - thing.depth / 2);
  rect.onclick = function() {
    thingRectClicked(thing.unique_id);
  };
  rect.setAttribute(
    "transform",
    "rotate(" + thing.rotation * 360 + ", " + thing.x + ", " + thing.y + ")" +
      "translate(" + thing.x + ", " + thing.y + ")")
  rect.appendChild(title);
  g.appendChild(rect);
}

function thing_svg_id(thing) {
  return "thingrect" + thing.unique_id;
}

var item_unique_id_counter = 1;

var ALL_THINGS = [];

function getThing(id) {
  for (var i = 0; i < ALL_THINGS.length; i++) {
    var thing = ALL_THINGS[i];
    if (thing.unique_id == id) {
      return thing;
    }
  }
}

// Show thing's description in the description element.  With no
// thing, just clear the description element.
function show_description(thing_id) {
  // Clear description:
  var desc_elt = document.getElementById("description");
  while (desc_elt.hasChildNodes()) {
    desc_elt.removeChild(desc_elt.firstChild);
  }
  if (!thing_id)
    return;
  var thing = getThing(thing_id);  
  var d = document.createElement("div");
  d.setAttribute("class", "description");
  desc_elt.appendChild(d);
  var name = document.createElement("div");
  name.setAttribute("class", "name");
  d.appendChild(name);
  name.appendChild(document.createTextNode(thing.name));
  if (thing.description) {
    var content = document.createElement("div");
    d.appendChild(content);
    // Description might be text or a URI.  We attempt to fetch it.
    // If that fails we insert it as text, otherwise we insert the
    // content if that makes sense.
    fetch("furnashings/" + thing.description).then(
      function(response) {
        console.log(response.status, response.statusText);
        if (!response.ok) {
          content.appendChild(document.createTextNode(thing.description));
          return;
        }
        response.text().then(
          function(txt) {
            // Assume HTML
            var dp = new DOMParser();
            var doc = dp.parseFromString(txt, "text/html");
            d.appendChild(doc.documentElement);
          }
        );
      },
      console.log);
  }
}

function thingRectClicked(thing_id) {
  console.log("clicked", thing_id);
  show_description(thing_id);
}

function enptySpaceClicked() {
  console.log("enptySpaceClicked");
  var desc_elt = document.getElementById("description");
  show_description(false);
 }
