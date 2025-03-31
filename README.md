# MapMyStuff

The goal of this project is to provide documentation for a shared
space (like the MIT Hobby Shop), in particular a floor plan and
locator.

It could be applied to other facilities if an SVG floor plan is
available.

Inkscape can be used to convert a PDF floor plan to SVG.  A python
script is provided to clean up the Inkscape SVG output.  It was
developed as an ad-hoc tool for a single floor plan.  It has not yet
been demonstrated to be generally useful with other floor plans or as
Inkscape evolves.  It can at least serve as a strating point if you
need to use Inkscape.

I've used MapMyStuff for three different facilities.  To see examples
of what MapMyStuff can do, you can view these on GitHub Pages:

See the map of the
[old MIT Hobby Shop](https://MarkNahabedian.github.io/MapMyStuff/Facilities/HobbyShop-DuPont/floor_plan.html)

See the map for
[the new MIT Hobby Shop in N51](https://MarkNahabedian.github.io/MapMyStuff/Facilities/HobbyShop-N51/floor_plan.html)

See the maps for
[CRMII](https://MarkNahabedian.github.io/MapMyStuff/Facilities/CRMII).


## Data

The floor plan of each facility is rooted in an SVG file.

Each furnashing that are layed out on the floor plan is deascribed by
a record in a JSON file.  That record should have these properties:

<dl>
  <dt>name
  <dd>The name of the item.

  <dt>unique_id
  <dd>A unique identifier string for the item.  This is used as the
      URL fragment for directly referring to the item.

  <dt>clustermarket_id
  <dd>For an item that can be reserved in ClusterMarket, the
      ClusterMarket identifier for that item.

  <dt>cssClass
  <dd>A CSS class that can be used to control the appearance (color,
      etc) of the item.

  <dt>width
  <dd>The width of a rectangular item when the user is facing it.

  <dt>depth
  <dd>The depth of a rectangular item -- the distance from the edge
      closest to the user to the edge furthest from the unit.

  <dt>x
  <dd>the x coordinate of the location of the center of the item in
      the coordinate system of the SVG floor plan file.

  <dt>y
  <dd>the y coordinate of the location of the center of the item in
      the coordinate system of the SVG floor plan file.

  <dt>rotation
  <dd>The facing direction of the person using the item, expressed as
      a fraction of a circle.

  <dt>description
  <dd>A textual description that will be rendered in the description
      box when the item is selected.

  <dt>description_uri
  <dd>A URL to a document that will be rendered in the description of
      box when the item is selected.

  <dt>path_d
  <dd>For an item that can't be drawn as a simple rectangle, the SVG
      `path` expression for drawing the item.
  
  <dt>booking_note
  <dd>A note about ClusterMarket related booking of the item.

  <dt>contents
  <dd>For items like cabinets, contents is a list of strings that can
      describe the contents of each shelf or drawer.

  <dt>measured
  <dd>Notes and details about the measurement of the item.
</dl>

Note that `x`, `y`, `width` and `depth` are expressed in the same
units as the SVG floor plan drawing, which is typically feet.
`measured` might include the measurement of the item in inches, which
would then be converted to feet for `x`, `y`, `width` and `depth`.
`measured` provides a record of the measurements actually taken from
the item.

