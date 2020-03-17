
# Ru7n with
#  python -m unittest test

import unittest
from cleanup_inkscape_svg import Box
from svg.path import Line


class TestBox (unittest.TestCase):
    box = Box(10, 30, 20, 40)

    def test_line_intersects_crosses(self):
        '''Line crosses Box with both end points outside.'''
        self.assertTrue(self.box.line_intersects(Line(25+45j, 5+25j)))

    def test_line_intersects_crosses(self):
        '''Both end points inside Box.'''
        self.assertTrue(self.box.line_intersects(Line(18+32j, 12+38j)))

    def test_line_start_inside_box(self):
        '''Start point inside Box.'''
        self.assertTrue(self.box.line_intersects(Line(15+32j, 25+25j)))

    def test_line_end_inside_box(self):        # *** FAILS
        '''End point inside Box.'''
        self.assertTrue(self.box.line_intersects(Line(25+25j, 15+32j)))

    def test_line_intersects_left(self):
        '''Line crosses Box but both end points are to the left of the box.'''
        self.assertFalse(self.box.line_intersects(Line(0+33j, 8+35j)))

    def test_line_intersects_right(self):
        '''Line crosses Box but both end points are to the right of the box.'''
        self.assertFalse(self.box.line_intersects(Line(22+33j, 28+35j)))

    def test_line_intersects_above(self):
        '''Line crosses Box but both end points are above the top of the box.'''
        self.assertFalse(self.box.line_intersects(Line(5+25j, 12+28j)))

    def test_line_intersects_below(self):
        '''Line crosses Box but both end points are below the bottom of the box.'''
        self.assertFalse(self.box.line_intersects(Line(15+42j, 8+50j)))

    def test_line_intersects_nocross(self):     # *** FAILS
        '''Line does not cross Box.'''
        self.assertFalse(self.box.line_intersects(Line(18+25j, 28+33j)))


# I need a way to visualize the test cases:
#
#           1         2         3
# 0123456789012345678901234567890
#
# ++++++++++++++++++++++++++++++  20
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++*---------*+++++++++  30
# ++++++++++|+++++++++|+++++++++
# ++++++++++|+++++++++|+++++++++
# ++++++++++|+++++++++|+++++++++
# ++++++++++|+++++++++}+++++++++
# ++++++++++|+++++++++|+++++++++
# ++++++++++|+++++++++|+++++++++
# ++++++++++|+++++++++|+++++++++
# ++++++++++|+++++++++|+++++++++
# ++++++++++|+++++++++|+++++++++
# ++++++++++*---------*+++++++++  40
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++  50


if __name__ == "__main__":
    unittest.main()

