# Boxes


from functools import reduce
import operator

import svg.path

from points import *


class Box (object):
    '''Box defines a rectangular region aligned in the viewPort.'''

    @classmethod
    def xywh(cls, x, y, width, height):
        '''Create a new box given top left X and Y and width and height.'''
        return Box(x, y, x + width, y + height)

    def __init__(self, minX, minY, maxX, maxY):
        self.minX = minX
        self.minY = minY
        self.maxX = maxX
        self.maxY = maxY

    def __eq__(self, other):
        return (self.minX == other.minX and
                self.minY == other.minY and
                self.maxX == other.maxX and
                self.maxY == other.maxY)

    def __hash__(self):
        return hash(repr(self))

    def __str__(self):
        return "x: %d..%d y: %d..%d" % (
            self.minX, self.maxX, self.minY, self.maxY)

    def __repr__(self):
        return("Box(%r, %r, %r, %r)" % (
            self.minX,
            self.minY,
            self.maxX,
            self.maxY))

    @property
    def width(self):
        return self.maxX - self.minX

    @property
    def height(self):
        return self.maxY - self.minY

    def corners(self):
        '''Returns the four corners of the box as points (satisfying isPoint).'''
        return [ point(self.minX, self.minY),
                 point(self.maxX, self.minY),
                 point(self.minX, self.maxY),
                 point(self.maxX, self.maxY) ]

    def d(self):
        '''Return an SVG path d attribute value for drawing the box.'''
        return "M %f %f H %f V %f H %f z" % (
            self.minX, self.minY,
            self.maxX,
            self.maxY,
            self.minX)

    def point_within(self, point):
        '''Returns True iff point is within the box.'''
        assert isPoint(point)
        x = point[0]
        y = point[1]
        return (self.minX <= x and
                self.maxX >= x and
                self.minY <= y and
                self.maxY >= y)

    def line_intersects(self, transform, svgLine):
        '''Returns True iff any of svgLine is within this Box.'''
        assert isinstance(svgLine, svg.path.Line)
        # The line does not cross the rectangle if all four corners
        # of self are on the same side of svgLine.
        p1 = transform.apply(cToV(svgLine.start))
        p2 = transform.apply(cToV(svgLine.end))
        v = p2 - p1
        sides = [ numpy.sign(numpy.cross(v, p - p1)[2])
                  for p in self.corners() ]
        if 4 == abs(reduce(operator.add, sides)):
            # All four corners are on the same side
            return False
        # We need to check the end points of the line
        return self.point_within(p1) or self.point_within(p2)

    def cubicBezier_intersects(self, transform, cb):
        '''Returns true iff the start, end and control points
        of cb are within the box.'''
        assert isinstance(cb, svg.path.CubicBezier)
        return (self.point_within(transform.apply(cToV(cb.start))) or
                self.point_within(transform.apply(cToV(cb.control1))) or
                self.point_within(transform.apply(cToV(cb.control2))) or
                self.point_within(transform.apply(cToV(cb.end))))

    
