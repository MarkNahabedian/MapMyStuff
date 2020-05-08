// Place things onto the floorplan.

function load_and_draw_things() {
  console.log("load_and_draw_things");
  var svgdoc = document.getElementById("floor_plan_svg").contentDocument;
  svgdoc.addEventListener("mousemove", Show_event_location);
  Promise.all([
    fetch_things("furnashings/things.json"),
    fetch_things("furnashings/metal_shop.json"),
    fetch_things("furnashings/wood_shop.json"),
    fetch_things("furnashings/offices.json")
  ]).then(function() {
    ALL_THINGS.sort(sort_item_item_compare);
    update_items_list(ALL_THINGS);
    if (document.location.hash) {
      select_item(document.location.hash.substring(1));
    }
  }, console.log);
}

function sort_item_item_compare(item1, item2) {
  var name1 = item1.name;
  var name2 = item2.name;
  if (name1 < name2) return -1;
  if (name1 > name2) return 1;
  return 0;
}

function fetch_things(path) {
  return fetch(path).then(function(response) {
    if (!response.ok) {
      console.log(response.statusText);
      return;
    }
    return response.text().then(
      function(txt) {
        try {
          var things = JSON.parse(txt);
          for(var i = 0; i < things.lengtrh; i++) {
            ALL_THINGS.push(things[i]);
          }
          draw_things(things, path);
        }
        catch (error) {
          throw (path + ": " + error);
        }
        return true;
      },
      console.log);
  });
}

function update_items_list(items) {
  var list_elt = document.getElementById("items");
  make_empty(list_elt);
  var do_list = function(container, things) {
    // things is a list containing item objects and strings.
    for (var i = 0; i < things.length; i++) {
      var item = things[i];
      var item_elt = document.createElement("div");
      item_elt.setAttribute("class", "item");
      if (typeof(item) === "string") {
        // Turn it into an item.
        item = {
          "name": item
        };
        things[i] = item;
      }
      item.list_element = item_elt;
      if (container == list_elt) {
        var a = document.createElement("a");
        a.setAttribute("href", "#" + item.unique_id);
        a.setAttribute("onclick",
                       "select_item('" + item.unique_id + "')");
        a.textContent = item.name;
        item_elt.appendChild(a);
      } else {
        item_elt.textContent = item.name;
      }
      if (item.contents && item.contents.length > 0) {
        var contents_elt = document.createElement("div");
        contents_elt.setAttribute("class", "container");
        item_elt.appendChild(contents_elt);
        do_list(contents_elt, item.contents);
      }
      container.appendChild(item_elt);
    }
  };
  do_list(list_elt, items);
}

function filter_items_list(filter_string) {
  // Initially we just test for mindless substring inclusion.
  filter_string = filter_string.toLowerCase();
  filter_items_list_(function(item) {
    return item.name.toLowerCase().indexOf(filter_string) >= 0;    
  });
}

function filter_items_list_(filter) {
  var show = function(item) {
    var elt = item.list_element;
    elt.setAttribute(
      "class", elt.getAttribute("class").replace(" hidden-item", ""));
  };
  var hide = function(item) {
    var elt = item.list_element;
    elt.setAttribute(
      "class", elt.getAttribute("class") + " hidden-item");
  };
  var do_item = function(item) {
    // Returns true iff item should be visible
    var any = false;
    if (filter(item)) {
      any = true;
    }
    if (item.contents) {
      for (var i = 0; i < item.contents.length; i++) {
        var itm = item.contents[i];
        if (do_item(itm)) {
          any = true;
        }
      }
    }
    if (any)
      show(item);
    else
      hide(item);
    return any;
  };
  ALL_THINGS.forEach(do_item);
}

function draw_things(things, from_path) {
  console.log('draw_things from ', from_path);
  var svgdoc = document.getElementById("floor_plan_svg").contentDocument;
  var g = svgdoc.getElementById("real-world");
  svgdoc.documentElement.onclick = enptySpaceClicked;
  var index = 0;
  while (index < things.length) {
    var thing = things[index];
    thing["from_file"] = from_path;
    if (!thing.unique_id) {
      thing["unique_id"] = item_unique_id_counter++;
    }
    ALL_THINGS.push(things[index]);
    try {
      draw_thing(svgdoc, g, thing);
    }
    catch (error) {
      console.log("Error while drawing " + thing.name +
                  "(" + from_path + " #" + index + "):" +
                  error);
    }
    index += 1;
  }
}

function draw_thing(svgdoc, g, thing) {
  var thing_group = svgdoc.createElementNS(g.namespaceURI, "g");
  thing_group.setAttribute("class", thing.cssClass);
  thing_group.setAttribute("id", thing_svg_id(thing));
  var shape;
  var title = svgdoc.createElementNS(g.namespaceURI, "title");
  title.textContent = thing.name;
  if (thing.path_d) {
    shape = svgdoc.createElementNS(g.namespaceURI, "path");
    shape.setAttribute("d", thing.path_d);
    thing_group.appendChild(shape);
  } else {
    shape = svgdoc.createElementNS(g.namespaceURI, "rect");
    shape.setAttribute("width", thing.width);
    shape.setAttribute("height", thing.depth);
    shape.setAttribute("x", - thing.width / 2);
    shape.setAttribute("y", - thing.depth / 2);
    var direction_tick = svgdoc.createElementNS(g.namespaceURI, "path");
    direction_tick.setAttribute("class", "direction-indicator");
    direction_tick.setAttribute(
      "d",
      "M 0 0 v " + (- thing.depth / 2)
    );
    thing_group.appendChild(shape);
    thing_group.appendChild(direction_tick);
  }
  shape.appendChild(title);
  // The vector-effect CSS property doesn't cascade.
  shape.setAttribute("class", thing.cssClass);
  shape.onclick = function(event) {
    if (!event)
      event = window.event;
    if (event.target !== this)
      return;
    thingRectClicked(thing);
  };
  thing_group.setAttribute(
    "transform",
    "rotate(" + thing.rotation * 360 + ", " + thing.x + ", " + thing.y + ")" +
      "translate(" + thing.x + ", " + thing.y + ")")
  g.appendChild(thing_group);
  thing.svg_element = thing_group;
}

function thing_svg_id(thing) {
  return "" + thing.unique_id;
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
  make_empty(desc_elt);
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
  // thing can be an item object or the unique_id of an item.
  // If null than any current selection is unselected.
  if (typeof(thing) === "string") {
    thing = getThing(thing);
  }
  console.log("select_item", thing);
  var svgdoc = document.getElementById("floor_plan_svg").contentDocument;
  // Clear existing selection
  if (selected_thing) {
    var elt = selected_thing.svg_element;
    elt.setAttribute("class", selected_thing.cssClass);
    target(selected_thing, false);
    selected_thing = null;
  }
  if (!thing) {
    show_description(false);
    document.location.hash = "";
    return;
  }
  selected_thing = thing;
  target(thing, true);
  document.location.hash = "#" + thing.unique_id;
  show_description(thing);
  var elt = selected_thing.svg_element;
  if (elt) {
    elt.setAttribute("class", selected_thing.cssClass + " selected");
  }
}

function thingRectClicked(thing) {
  select_item(thing);
  Show_event_location(event);
}

function enptySpaceClicked(event) {
  if (!event)
    event = window.event;
  if (event.target !== this)
    return;
  select_item();
  Show_event_location(event);
}

// Draw (or remove) a target circle around the specified item.
function target(item, doit=false) {
  if (doit) {
    var item_elt = item.svg_element;
    var doc = item_elt.ownerDocument;
    var bbox = item_elt.getBBox();
    var centerX = bbox.x + bbox.width / 2;
    var centerY = bbox.y + bbox.height / 2;
    var radius = Math.max(bbox.width, bbox.height) / 2;
    var g = doc.createElementNS(item_elt.namespaceURI, "g");
    var circle = function(multiplier, cls) {
      var c = doc.createElementNS(item_elt.namespaceURI, "circle");
      g.appendChild(c);
      c.setAttribute("cx", centerX);
      c.setAttribute("cy", centerY);
      c.setAttribute("r", radius * multiplier);
      c.setAttribute("class", cls);
    };
    circle(1.3, "target");
    // circle(1.6, "target");
    item_elt.appendChild(g);
    item.target_indicator = g;
  } else {
    if (item.target_indicator) {
      item.target_indicator.parentElement.removeChild(item.target_indicator);
      item.target_indicator = null;
    }
  }
}

function Show_event_location(event) {
  var container = document.getElementById("floor_plan_svg");
  var svgdoc = container.contentDocument;
  var showX = document.getElementById("show-pointer-x");
  var showY = document.getElementById("show-pointer-y");
  var g = svgdoc.getElementById("real-world");
  var trans = g.getScreenCTM().inverse();
  var point = new DOMPoint(event.clientX, event.clientY);
  xformed = point.matrixTransform(trans);
  showX.textContent = xformed.x.toFixed(3);
  showY.textContent = xformed.y.toFixed(3);
}

function make_empty(element) {
  while (element.hasChildNodes()) {
    element.removeChild(element.firstChild);
  }
}
