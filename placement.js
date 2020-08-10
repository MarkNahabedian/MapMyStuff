//   -*- js-indent-level: 2; -*-

// Place things onto the floorplan.

function load_and_draw_things() {
  console.log("load_and_draw_things");
  var svgdoc = document.getElementById("floor_plan_svg").contentDocument;
  svgdoc.addEventListener("mousemove", Show_event_location);
  Promise.all([
    fetch_things("furnashings/things.json"),
    fetch_things("furnashings/metal_shop.json"),
    fetch_things("furnashings/wood_shop.json"),
    fetch_things("furnashings/offices.json"),
    fetch_things("furnashings/welding_area.json")
  ]).then(function() {
    ALL_THINGS.sort(sort_item_item_compare);
    update_items_list(ALL_THINGS);
    if (document.location.hash) {
      select_item(document.location.hash.substring(1));
    }
    add_download_link();
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
          for (let thing of things) {
            thing.from_file = response.url;
            ALL_THINGS.push(thing);
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

function add_download_link() {
  var svgdoc = document.getElementById("floor_plan_svg").contentDocument;
  var link = document.getElementById("download_floor_plan");
  if (link == null)
    return;
  var serializer = new XMLSerializer(); 
  var svg = serializer.serializeToString(svgdoc);
  var data = new Blob([svg], { type: "image/svg+xml" });
  var url = window.URL.createObjectURL(data);
  link.href = url;
  console.log("Download link set");
}

function draw_things(things, from_path) {
  console.log('draw_things from ', from_path);
  var svgdoc = document.getElementById("floor_plan_svg").contentDocument;
  var g = svgdoc.getElementById("real-world");
  svgdoc.documentElement.onclick = enptySpaceClicked;
  var index = 0;
  while (index < things.length) {
    var thing = things[index];
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
  if (!(isNumber(thing.x) && isNumber(thing.y)))
    return;
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
//
// Because drawing the selected item indicator in the page overlay
// requires that the display box already be sized, this returns a
// Promise whose resolution can be used to trigger drawing of the
// selected item indicator.
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
  if (description) {
    var content = document.createElement("div");
    d.appendChild(content);
    // Description might be text or a URI.  If it contains whitespace
    // (likely in a textual description) then we know it's not a URI.
    if (description.indexOf(" ") >= 0) {
      content.appendChild(document.createTextNode(description));
      return Promise.resolve(null);
    }
    // Otherwise, we attempt to fetch it.  If that fails we insert it as
    // text, otherwise we insert the content of the fetched document.
    let test_uri = new URL(thing.description, thing.from_file);
    return fetch(test_uri /*, method: "HEAD" */ ).then(
      function(response) {
        console.log(response.status, response.statusText);
        if (!response.ok) {
          content.appendChild(document.createTextNode(thing.description));
          return Promise.resolve(null);
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
  // If no description, then show contents
  var contents = thing.contents;
  if (contents) {
    var list = document.createElement("ul");
    d.appendChild(list);
    for (c of contents) {
      var li = document.createElement("li");
      list.appendChild(li);
      li.textContent = c.name;
    }
    // Drop through to return resolved Promise.
  }
  return Promise.resolve(null);
}

var selected_thing = null;

window.onresize = function () {
  select_item(selected_thing);
};

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
  show_description(thing).then(wait(100)).then(() => target(thing, true));
  // Give the layout a chance to update before this:
  // window.setTimeout(target, 300, thing, true);
  document.location.hash = "#" + thing.unique_id;
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

// Make it easy to find the selected item on the floor plan.
function target(item, doit=false) {
  var overlay = document.getElementById("selection-overlay");
  make_empty(overlay);
  if (!doit) {
    return;
  }
  var desc_box = document.getElementById("description");
  var desc_bbox = desc_box.getBoundingClientRect();
  var obj_bbox = document.getElementById("floor_plan_svg").getBoundingClientRect();
  // selected_bbox is in a different document (contained within an
  // object element).  We need to offset by the edges of the object
  // element.
  var selected_bbox = item.svg_element.getBoundingClientRect();
  var sel_centerX = (selected_bbox.left + selected_bbox.right) / 2;
  var sel_centerY = (selected_bbox.top + selected_bbox.bottom) / 2;
  var centerX = window.scrollX + sel_centerX; // + obj_bbox.left;   WHY DOES ADDIING THIS NOT GIVE THE RIGHT X?
  var centerY = window.scrollY + sel_centerY + obj_bbox.top;
  // WHY DO WE NEED THIS KLUDGE TO GET THE Y COORDINATE RIGHT
  centerY -= 20;
  var radius = 1.2 * bbox_radius(selected_bbox);
  var c = document.createElementNS(overlay.namespaceURI, "circle");
  c.setAttribute("cx", centerX);
  c.setAttribute("cy", centerY);
  c.setAttribute("r", radius);
  overlay.appendChild(c);
  var anchorX = window.scrollX + ((desc_bbox.left + desc_bbox.right) / 2);
  var anchorY = window.scrollY + desc_bbox.bottom;
  var cpp = circle_perimeter_point(centerX, centerY, radius, anchorX, anchorY)
  var p = document.createElementNS(overlay.namespaceURI, "path");
  p.setAttribute("d",
                 "M " + anchorX + " " + anchorY +
                 " L " +
                 (centerX - cpp[0]) + " " + (centerY - cpp[1])
                );
  overlay.appendChild(p);
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
  if (LOG_PATHS_AT_POINT) {
    find_surrounding_paths(svgdoc, point, PATHS_AT_POINT_METRIC);
  }
}

function bbox_size(bbox) {
  return Math.max(Math.Abs(bbox.right - bbox.left),
                  Math.abs(bbox.bottom - bbox.top));
}

function bbox_area(bbox) {
  return (bbox.right - bbox.left) * (bbox.bottom - bbox.top);
}

var LOG_PATHS_AT_POINT = false;
var PATHS_AT_POINT_METRIC = bbox_area;

function find_surrounding_paths(svgdoc, point, metric) {
  var x = point.x;
  var y = point.y;
  var found = [];
  function cmp(a, b) {
    if (metric(a) < metric(b)) return -1;
    if (metric(a) > metric(b)) return 1;
    return 0;
  }
  for (var path of svgdoc.getElementsByTagName("path")) {
    var bbox = path.getBoundingClientRect();
    if (x < bbox.left) continue;
    if (x > bbox.right) continue;
    if (y < bbox.top) continue;
    if (y > bbox.bottom) continue;
    found.push(path);
  }
  found.sort(cmp);
  for (var path of found) {
    console.log(path);
  }
}


function make_empty(element) {
  while (element.hasChildNodes()) {
    element.removeChild(element.firstChild);
  }
}

function wait(ms) {
  return function(x) {
    return new Promise(resolve => setTimeout(resolve, ms, x));
  };
}

function bbox_radius(bbox) {
  var hw = bbox.width / 2;
  var hh = bbox.height / 2;
  return Math.sqrt(hw * hw + hh * hh);
}

function circle_perimeter_point(centerX, centerY, radius, otherX, otherY) {
  var angle = Math.atan2(centerY - otherY, centerX - otherX);
  return [radius * Math.cos(angle),
          radius * Math.sin(angle)];
}

function isNumber(n) {
  return (typeof n == "number");
}

