# Coordinate system transformations.

import re
import math
import numpy
import numpy.linalg

from points import *


class Transform(object):
    '''Coordinate system transformations.'''
    DEGREES_PER_RADIAN = 360 / (2 * math.pi)

    @classmethod
    def identity(cls):
        return cls(numpy.array(
            [[1, 0, 0],
             [0, 1, 0],
             [0, 0, 1]]))

    @classmethod
    def matrix(cls, a, b, c, d, e, f):
        return cls(numpy.array(
            [[a, c, e],
             [b, d, f],
             [0, 0, 1]]))

    @classmethod
    def translate(cls, x, y):
        return cls(numpy.array(
            [[1, 0, x],
             [0, 1, y],
             [0, 0, 1]]))

    @classmethod
    def scale(cls, scaleX, scaleY):
        return cls(numpy.array(
            [[scaleX, 0, 0],
             [0, scaleY, 0],
             [0, 0, 1]]))

    @classmethod
    def rotate(cls, angle):
        '''Angle specified in degrees.'''
        a = angle / cls.DEGREES_PER_RADIAN
        sinA = math.sin(a)
        cosA = math.cos(a)
        return cls(numpy.array(
            [[cosA, - sinA, 0],
             [sinA, cosA, 0],
             [0, 0, 1]]))

    def __init__(self, matrix):
        self.matrix = matrix

    def __repr__(self):
        return "Transform(%r)" % self.matrix

    def inverse(self):
        return Transform(numpy.linalg.inv(self.matrix))

    def toSVG(self):
        a = self.matrix[0][0]
        b = self.matrix[1][0]
        c = self.matrix[0][1]
        d = self.matrix[1][1]
        e = self.matrix[0][2]
        f = self.matrix[1][2]
        if (a == d and b == -c
            and e == 0 and f == 0 and
            (list(self.matrix[2]) == [0, 0, 1])):
            return "rotate(%f)" % (math.acos(a) * self.__class__.DEGREES_PER_RADIAN)
        if (a == 1 and b == 0 and
            c == 0 and d == 1 and
            (list(self.matrix[2]) == [0, 0, 1])):
            return "translate(%f,%f)" % (e, f)
        if (c == 0 and e == 0 and
            b == 0 and f == 0 and
            (list(self.matrix[2]) == [0, 0, 1])):
            return "scale(%f,%f)" % (a, d)
        return "matrix(%f,%f,%f,%f,%f,%f)" % (a, b, c, d, e, f)

    def apply(self, point):
        '''Applies the transform to the point, returning a point that satisfies isPoint.'''
        if isPoint(point):
            return numpy.matmul(self.matrix, point)
        if isinstance(point, complex):
            return self.apply(cToV(point))
        assert False, "Unsupported point type: %r" % point

    def compose(self, other):
        return Transform(numpy.matmul(self.matrix, other.matrix))


# matrix(0.06,0,0,0.06,7,7)
TRANSFORM_REGEXP = re.compile("(?P<type>[a-zA-Z-_]+)[(](?P<args>[^)]*)[)]")

def parse_transform(transform_string):
    '''Parse an SVG trransform attribute.  Returns a Transform.'''
    # *** Does not yet consider multiple transformations in a single attribute string.
    m = TRANSFORM_REGEXP.match(transform_string)
    if not m:
        return
    if m.group("type") == "matrix":
        return Transform.matrix(*[float(x.strip()) for x in m.group("args").split(",")])
    if m.group("type") == "translate":
        return Transform.translate(*[float(x.strip()) for x in m.group("args").split(",")])
    print("Unsupported transform %s" % transform_string)
    return

             
