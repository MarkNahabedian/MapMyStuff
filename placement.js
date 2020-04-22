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
  g.onclick = enptySpaceClicked;
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
  rect.appendChild(title);
  rect.setAttribute("class", thing.cssClass);
  rect.setAttribute("id", thing_svg_id(thing));
  rect.setAttribute("x", thing.x);
  rect.setAttribute("y", thing.y);
  rect.setAttribute("width", thing.width);
  rect.setAttribute("height", thing.depth);
  rect.setAttribute("x", - thing.width / 2);
  rect.setAttribute("y", - thing.depth / 2);
  rect.onclick = function(event) {
    if (!event)
      event = window.event;
    if (event.target !== this)
      return;
    thingRectClicked(thing);
  };
  rect.setAttribute(
    "transform",
    "rotate(" + thing.rotation * 360 + ", " + thing.x + ", " + thing.y + ")" +
      "translate(" + thing.x + ", " + thing.y + ")")
  g.appendChild(rect);
  thing.svg_element = rect;
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
function show_description(thing) {
  // Clear description:
  var desc_elt = document.getElementById("description");
  while (desc_elt.hasChildNodes()) {
    desc_elt.removeChild(desc_elt.firstChild);
  }
  if (!thing)
    return;
  var d = document.createElement("div");
  d.setAttribute("class", "description");
  desc_elt.appendChild(d);
  var name = document.createElement("div");
  name.setAttribute("class", "name");
  d.appendChild(name);
  name.appendChild(document.createTextNode(thing.name));
  var description = thing.description;
  if (!description)
    return;
  var content = document.createElement("div");
  d.appendChild(content);
  // Description might be text or a URI.  If it contains whitespace
  // (likely in a textual description) then we know it's not a URI.
  if (description.indexOf(" ") >= 0) {
    content.appendChild(document.createTextNode(description));
    return;
  }
  // Otherwise, we attempt to fetch it.  If that fails we insert it as
  // text, otherwise we insert the content of the fetched document.
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

var selected_thing = null;

function select_item(thing) {
  console.log("select_item", thing);
  var svgdoc = document.getElementById("floor_plan_svg").contentDocument;
  // Clear existing selection
  if (selected_thing) {
    var elt = selected_thing.svg_element;
    elt.setAttribute("class", selected_thing.cssClass);
    selected_thing = null;
  }
  if (!thing) {
    show_description(false);
    return
  }
  selected_thing = thing;
  show_description(thing);
  var elt = selected_thing.svg_element;
  if (elt) {
    elt.setAttribute("class", selected_thing.cssClass + " selected");
  }
}

function thingRectClicked(thing) {
  console.log("clicked", thing);
  select_item(thing);
}

function enptySpaceClicked(event) {
  if (!event)
    event = window.event;
  if (event.target !== this)
    return;
  console.log("enptySpaceClicked");
  select_item();
 }
