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

Each furnashing that is layed out on the floor plan is deascribed by
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


## Tools

This repository also includes some tools for local maintenance,
testing, and debugging.


### web_server.py

`web_server.py` is a python3 script that runs a web server locally.
This allows the floor plans to be viewed locally, before changes are
committed or pushed.


### bump.py

`bump.py` provides a command line tool for adjusting the `x` and `y`
coordinates of a furnashing in a floor plan.

It finds the items specified by `unique_id` in the specified JSON
files and adjusts their `x` and `y` positions as specified.

```
./bump.py --help
usage: bump [-h] [-x X] [-y Y] [-dx DX] [-dy DY] [-file FILES] items [items ...]

Adjust the x and y properties of the specified items in the specified JSON files

positional arguments:
  items        unique_id of the items to modify

optional arguments:
  -h, --help   show this help message and exit
  -x X         Specify an absolute X coordinate for the specified items
  -y Y         Specify an absolute Y coordinate for the specified items
  -dx DX       Specify a change for the X coordinate for the specified items
  -dy DY       Specify a change for the Y coordinate for the specified items
  -file FILES  Specifies a JSON file to modify. Can be specified multiple times.
```


### git-hooks/pre-commit.py

`git-hooks/pre-commit.py` is a python3 script that can serve as a git
`pre-commit` hook which verifies the syntax of a JSON file and warns
if any of the properties in it are not recognized, perhaps due to a
typo.

It can be installed as your clone's pre-commit hook

```
ln -s -F `pwd`/git-hooks/pre-commit.py .git/hooks/pre-commit
```

or used on the command line:

```
git-hooks/pre-commit.py  Facilities/HobbyShop-N51/furnashings/wood.json
Facilities/HobbyShop-N51/furnashings/wood.json: Expecting ',' delimiter: line 823 column 9 (char 24704)
```

Note that a JSON file must be syntactically correct before the
property names can be checked:

```
git-hooks/pre-commit.py  Facilities/HobbyShop-N51/furnashings/wood.json
Facilities/HobbyShop-N51/furnashings/wood.json: unsupported properties: ['dept']
```


### ensure_identifiers.py

`ensure_identifiers.py` is a python3 script that will ensure that each
item has a `unique_id` property.  Missing unique identifiers will be
added.  The unique ids generated will be of the form `_x_*0000*`,
where `*0000*` is a four digit number greater than any other generated
unique id in any JSON file in the current working directory.

