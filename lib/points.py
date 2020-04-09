# Functions for dealing with the various representations of points we
# need to deal with.
#
# svg.path represents points as complex numbers.
#
# To use numpy's matrix operations we need to represent a point as a
# one dimentionsl numpy.array.

import numpy


def point(x, y):
    "Constructs a point suitable for numpy arithmetic."
    return numpy.array([x, y, 1])


def isPoint(p):
    return (isinstance(p, numpy.ndarray) and
            p.shape == (3,))


def cToV(c):
    '''Represents a complex number as a one dimensional two element numpy array.'''
    return point(cPointX(c), cPointY(c))


def cPointX(c):
    '''Return the X component of a coordinate represented as a complex number.'''
    return c.real


def cPointY(c):
    '''Return the Y component of a coordinate represented as a complex number.'''
    return c.imag
