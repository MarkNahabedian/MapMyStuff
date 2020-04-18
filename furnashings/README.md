The JSON files in this directory list and describe the tools,
machinery and furnashings of MIT's Hobby Shop.  Below we use "item" as
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

gives a brief descriptive name for the item.


## width

To draw an item on the floor plan we need to know its size.  The width
property describes how wide the item is in feet, from the point of
view of someone standing at the item and using it.  For a workbench
this can be subjective, but for a machine like a table saw the width
is measured perpendicular to the rip fence.

<pre>
     "width": 6,
</pre>

## Depth

The dept of an item is the distance between the edge of the item
closest to the user to the edge firthest away.


## cssClass

The cssClass property provides a way tocontrol the appearance of the
item on the floor plan.  The CSS presentation properties associated
with these classes are defined in the stylesheet thing_styles.css.

Currently we have so few items described that they all have a cssClass
of "thing".

     "cssClass": "thing",

We envision defining different appearances for machines versus
workbenches, for example.


# Locatioon Properties

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
center so that specifying a rotation for the item does not also its
position.


## y

Like the x property, the y property is expresse3d in feet.  The y
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


# Special Purpose Properties

Additional properties might be provided to provide a more detailed etc.,
descriptionof an item,link to user manuals
