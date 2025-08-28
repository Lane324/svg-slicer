"""
Tests gcode_generator
"""

import pytest

import svg2gcode.gcode_generator


@pytest.mark.parametrize(
    "start,end,expected_direction",
    [
        (0 + 0j, 1 + 0j, 0.0),
        (0 + 0j, 1 + 1j, 45.0),
        (0 + 0j, 0 + 1j, 90.0),
        (0 + 0j, -1 + 1j, 135.0),
        (0 + 0j, -1 + 0j, 180.0),
        (0 + 0j, -1 - 1j, 225.0),
        (0 + 0j, 0 - 1j, 270.0),
        (0 + 0j, 1 - 1j, 315.0),
    ],
)
def test_eval(start: complex, end: complex, expected_direction: float):
    assert svg2gcode.gcode_generator.get_direction(start, end) == expected_direction
