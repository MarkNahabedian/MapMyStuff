# A Floor PLan for the Hobby Shop

We got a drawing of the floor plan of the DuPont basement in PDF
format from MIT Facilities.

Inkscape was used to convert that PDF file to SVG.

This code cleans up that SVG and crops it to the boundaries of the
Hobby Shop space.


# Details

There are a number of artifacts of the floor plan that we attempt to
improve.


## Spurious Attributes

Inkscape adds attributes that are not relevant to most SVG
processors.  ATTRIBUTES_TO_REMOVE is a list of such attributes which
are to be removed to decrease the amount of noise in the SVG file we
wish to produce.


## Stylesheet

All of the SVG drawing elements output by inkscape have explicit style
attributes, greatly increasing the size of the file and makinig it
harder to read.

The source line

<pre>
    add_stylesheet(doc, extract_styles(doc))
</pre>

abstracts all of those style attributes by defining a CSS class for
each unique combination of CSS style property values and adds that
stylesheet to the output file.


## Overly Broad Scope

The floor plan we were given covers all of the basement of W31
(DuPont).  We only care about the Hobby Shop.  The rest is unnecessary
and removing it reduces the size of the SVG file by an order of
magnitude.

The command line arguments --grid_spacing, --clip_box, and
--show_clip_box can be used to identify the relevant range of X and Y
expressed in top level SVG viewBox coordinates.

Once a suitable box is identified, the --clip_svg_viewbox agument can
be used to update the viewBox attribute of the SVG element to that box
and the --clip argument can be used to remove drawing elements that
are outside of that box.  Any SVG group elements that are left empty
after drawing elements are removed are also removed.


## Probing

The --boxes_file command line argument can be used to identify
rectangular regions of the drawing (as X and Y bounds in the SVG
viewBox coordinate system).  This can be helpful for finding various
regions of the drawing.  an XML comment is added to any SVG path
element that is within any of the specified boxes.

This was helpful in identifying which CSS style was used to remove the
meaningless text described below, and also to find the graphics
responsible for showing the scale of the drawing.


## Meaningless Text

The Facilities floor plan contains text that, though presumably
meaningful to Facilities staff, are meaningless to me, and just add
clutter.

Unfortunately, these are not SVG text elements but instead are drawn
as SVG paths.

I first tried to define bounding Boxes around this "text" and deleting
any SVG path elements that are wholly contained in those boxes.  This
didn't work though since the "text" overlaps useful floorplan
elements.

I found that all of this text uses the same CSS styling.
Unfortunately that same styleiing is used in the drawing of the scale
graphic.

We deal with this problem by creating copies of any CSS classes used
to style the drawing scale graphic and using the -hide_classes command
line argument to make anything styled with class style4 invisible.


## Making the Drawing Lines Heavier

The lines in the floor plan come out too light.  By adding

<pre>
    vector-effect: non-scaling-stroke;
</pre>

the lines come out a bit darker.  Further improvements might be made
by manual editing of stroke-width.


## Real-World Scaling

Box probing as described above was used to identify the graphical
elements that depict the scale of the drawing.  These elements can be
extracted to a separate group and translated to be closer to the part
of the drawing that we intend to keep.

By examining the transforms of the text elements in the g.drawingScale
element it can be determined that 16 real world feet correspond to 45
units in the SVG viewBox coordinate system.

The -grid_real_world_size command line argument can be used to specify
how many real world units (e.g. feet) is represented by the space
between two successive grid lines.


## Manual Post-Processing of the Converted SVG File

Here's the command that was used to process the Inkscape output:

<pre>
python3 cleanup_inkscape_svg.py \
    -grid_spacing 45 \
    -clip_box 705 467 964 605 \
    -drawing_scale_box 490 900 650 950 \
    -scale_relocation 250 -290 \
    -clip \
    -hide_classes=style4 \
   -clip_svg_viewbox \
    -increase_viewbox_height 200 \
    -grid_real_world_size 16
</pre>

There are improvements that can be made on the output of this command
that are easier to do by manual editing than by thring to figure out
useful command line arguments.





