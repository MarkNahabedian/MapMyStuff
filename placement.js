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

function draw_things() {
  console.log('draw_things');
  var g = document.getElementById("real-world");
  var index = 0;
  while (index < THINGS.length) {
    thing = THINGS[index];
    draw_thing(g, thing, index);
    index += 1;
  }
}

function contentLoaded() {
  console.log('contentLoaded');
  draw_things();
}

