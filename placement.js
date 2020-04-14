// Place things onto the floorplan.

function draw_thing(g, thing, index) {
  console.log("draw_thing " + thing.name);
  var rect = document.createElement("rect");
  var title = document.createElement("title");
    title.textContent = thing.name;
  rect.setAttribute("Class", thing.cssClass);
  rect.setAttribute("x", thing.x);
  rect.setAttribute("y", thing.y);
  rect.setAttribute("width", thing.width);
  rect.setAttribute("height", thing.depth);
  rect.setAttribute("x", - thing.width / 2);
  rect.setAttribute("y", - thing.depth / 2);
  // We should eventually figure out how to simplify drawing using cx
  // and cy for the rotation transformation.
  rect.setAttribute("transform",
                    "rotate(" + thing.rotation + ", 0, 0)" +
                    "translate(" + thing.x + ", " + thing.y + ")")
  rect.appendChild(title);
  g.appendChild(rect);
}

function draw_things(things) {
  console.log('draw_things');
  var svgdoc = document.getElementById("floor_plan_svg").contentDocument;
  var g = svgdoc.getElementById("real-world");
  var index = 0;
  while (index < things.length) {
    thing = things[index];
    draw_thing(g, thing, index);
    index += 1;
  }
}

function fetch_things(path) {
  console.log("fetch_things " + path)
  fetch(path).then(function(response) {
    if (!response.ok) {
      console.log(response.statusText);
      return;
    }
    response.text().then(
      function(txt) {
        things = JSON.parse(txt);
        draw_things(things);
      },
      console.log);
  });
}

function contentLoaded() {
  console.log('contentLoaded');
  fetch_things("furnashings/things.json");
}

