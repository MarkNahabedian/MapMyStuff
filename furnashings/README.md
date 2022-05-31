The JSON files in this directory list and describe the tools,
machinery and furnishings of MIT's Hobby Shop.  Below we use "item" as
a generic term for any of these.

Each JSON object describes one such item. Each has a number of JSON
properties, some of which provide information about the item itself
and others describe its location in the shop.


# Common Descriptive Properties

## name

The name property, e.g.

<pre>
     "name":"table saw",
</pre>

gives a brief descriptive name for the item.  This property is
presented in the tooltip when hovering over the item and is centered
at the top of the description box when the item is clicked on.


## cssClass

The cssClass property provides a way to control the appearance of the
item on the floor plan.  The CSS presentation properties associated
with these classes are defined in the stylesheet thing_styles.css.

     "cssClass": "thing",

This allows us to define different appearances for machines versus
workbenches, for example.

The currently defined CSS classes for distinguishing types of items are

machine
: a piece of heavymachinery

station
: a place where one might do work, often focused on a particular set
of tasks, that isn't a heavy machine

storage
: cabinets, shelves, drawers, wood racks, etc.

furnature
: desks, couches, shairs, etc.

thing
: anything else


## unique_id

A unique_id can be provided So that items can be referred to from the
descriptions of other items.  The unique_id will be used as the "id"
attribute of the SVG group element that represents the item on the
floor plan.

Here's an example of how to link to another item from an HTML
description so that that item will be selected when its link is
clicked on:

<pre> <![CDATA[
  <a href="#unique_id"
     onclick="select_item('unique_id')">
    anchor text
  </a>.
]]></pre>

NOTE: For links within item descriptions, the onclick attribute is
required since I've not yet figured out what event to handle to terget
fragent links within the current document to refer to SVG elements.

Items with permanent unique_id properties can be linked to directly
using that unique id as a URL fragment, for example
<a href="../floor_plan.html#SI_154CH089">
../floor_plan.html#SI_154CH089
</a>.


# Shape

## Rectangle

We assume that most items are rectangular, or at least can be
represented by a rectangular footprint.

We draw those items that can be represented by a rectangle with an SVG
rect element for which we must provide a width and height.

We also add an indicator to show the rotational orientation of the
item.  This is just a line drawn from the center of the rectangle to
the "operator" side of the item.  Using the table saw as an example,
this would be the infeed side.


### width

To draw an item on the floor plan we need to know its size.  The width
property describes how wide the item is in feet, from the point of
view of someone standing at the item and using it.  For a workbench
this can be subjective, but for a machine like a table saw the width
is measured perpendicular to the rip fence from the infeed side of the
saw,

<pre>
     "width": 6,
</pre>

### depth

The dept of an item is the distance between the edge of the item
closest to the user to the edge farthest away.


## Non-rectangular Shapes

For items that can't be modeled by a rectange we use a closed SVG path
element.  That path element's origin will be placed at the specified X
and Y coordinate and the shape of the path should consider what

<pre>
  "direction": 0
</pre>

is.


### path_d

The path_d property provides the "d" attribute of the SVG path
representing the item.


# Location Properties

An item's location properties are used to position it on the floor plan.

The Hobby Shop is roughly rectangular, but, from the point of view of
one who has just walked in the entrance, the wall all of the way to
the left (left wall) and the wall along the corridor (front wall) are
the only ones that are straight and extend over the entire shop.
These are the walls we measure from when placing an item on the floor
plan.


## x

The x property is expressed in feet and measures the distance from the
left wall of the shop to the center of the item.  We measure to the
center so that specifying a rotation for the item does not also change
its position.


## y

Like the x property, the y property is expressed in feet.  The y
property measures the distance from the front wall of theHobby Shop to
the center of the item.


## rotation

The rotation of an item is used to change how it is ortiented with
respect to the walls of the shop.  Rotatioin is expressed in fractions
of a whole circle, so for a rotation of 90 degrees the rotation would
be 0.25:

<pre>
     "rotation": 0.25
</pre>

A rotation of 0 orients the item such that its width is parallel to
the x axis of the coordinate grid that's used for item placement and
the user of the item's back is towards the front wall of the shop.


# Other Properties


## description

The description is used to provide further information about the item.
It should be a plain text string.


## description_uri

Alternatively, the item can be described by an external HTML file.
This property provides the URL for that file.


# Properties Related to Clustermarket Booking

## clustermarket_id

This property is a unique identifier used to refer to an item in the
Clustermarket booking web site.  Because of the way that the Hobby
Shop is set up, several items might share the same clustermarket_id.
For example, the entire ewelding area, including the sheet metal break
and sheer, are booked using a single clustermarket_id for the entire
welding area.

## booking_note

This property is used to provide information about how the item is
booked.  Such details might be used, for exampple, in the wood shop,
where booking any bench allows access to any of the woodworking
machinery.


# Special Purpose Properties

Additional properties might be provided to provide a more detailed etc.,
descriptionof an item,link to user manuals


## contents

Some items are storage cabinents which are not interesting in
themselves but are interesting because of their contents.  The value
of the contents property is a list, each element of which can be a
simple string, e.g. "sandpaper", or an item.  The contents of an item
is included in outline form in the list of all items below the floor
plan.
