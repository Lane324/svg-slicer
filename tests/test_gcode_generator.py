"""
Tests gcode_generator
"""

import unittest

import pytest
import svgpathtools

import svg2gcode.gcode_generator


@pytest.fixture()
def mock_circle_path() -> tuple[svgpathtools.Arc, svgpathtools.Arc]:
    """"""
    circle_path = (
        svgpathtools.Arc(
            start=(40 + 50j),
            radius=(10 + 10j),
            rotation=0.0,
            large_arc=True,
            sweep=False,
            end=(60 + 50j),
        ),
        svgpathtools.Arc(
            start=(60 + 50j),
            radius=(10 + 10j),
            rotation=0.0,
            large_arc=True,
            sweep=False,
            end=(40 + 50j),
        ),
    )
    return circle_path


def test_init_gcode_point():
    """Tests that a GcodePoint initailizes correctly"""

    num = 1 + 2j
    raised = True
    point = svg2gcode.gcode_generator.GcodePoint(num, raised)
    assert point.point == num
    assert point.raised == raised


def test_gcode_point_get_gcode_not_raised(monkeypatch: pytest.MonkeyPatch):
    """Tests that a GcodePoint correctly creates gcode when not raised"""
    monkeypatch.setattr("svg2gcode.gcode_generator.START_X", 0)
    monkeypatch.setattr("svg2gcode.gcode_generator.START_Y", 0)
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_X", 10)
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_Y", 10)

    num = 1 + 2j
    point = svg2gcode.gcode_generator.GcodePoint(num, False)
    gcode = point.get_gcode(1)

    expected_gcode = [f"G1 X{num.real} Y{num.imag}\n"]

    assert gcode == expected_gcode


def test_gcode_point_get_gcode_raised(monkeypatch: pytest.MonkeyPatch):
    """Tests that a GcodePoint correctly creates gcode when raised"""
    monkeypatch.setattr("svg2gcode.gcode_generator.START_X", 0)
    monkeypatch.setattr("svg2gcode.gcode_generator.START_Y", 0)
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_X", 10)
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_Y", 10)

    num = 1 + 2j
    point = svg2gcode.gcode_generator.GcodePoint(num, True)
    gcode = point.get_gcode(1)

    expected_gcode = [
        svg2gcode.gcode_generator.LIFT_GCODE,
        f"G0 F{svg2gcode.gcode_generator.TRAVEL_FEEDRATE}\n",
        f"G1 X{num.real} Y{num.imag}\n",
        f"G0 F{svg2gcode.gcode_generator.NORMAL_FEEDRATE}\n",
        svg2gcode.gcode_generator.UNLIFT_GCODE,
    ]
    assert gcode == expected_gcode


@pytest.mark.parametrize(
    "start,end,expected_direction",
    [
        (0 + 0j, 0 + 0j, 0.0),
        (0 + 0j, 1 + 0j, 0.0),  # +x 0y
        (0 + 0j, 1 + 1j, 45.0),  # +x 0y
        (0 + 0j, 0 + 1j, 90.0),  # 0x +y
        (0 + 0j, -1 + 1j, 135.0),  # -x +y
        (0 + 0j, -1 + 0j, 180.0),  # -x 0y
        (0 + 0j, -1 - 1j, 225.0),  # -x -y
        (0 + 0j, 0 - 1j, 270.0),  # 0x -y
        (0 + 0j, 1 - 1j, 315.0),  # +x -y
    ],
)
def test_getting_direction_between_points(
    start: complex, end: complex, expected_direction: float
):
    """Test that getting the direction between 2 points returns the correct degrees"""
    assert svg2gcode.gcode_generator.get_direction(start, end) == expected_direction


@pytest.mark.parametrize(
    "x,y,scale",
    [
        (10.0, 10.0, 1.0),  # same size
        (20.0, 20.0, 0.5),  # x double y double
        (20.0, 10.0, 0.5),  # x double y same
        (10.0, 20.0, 0.5),  # x same y double
        (5.0, 5.0, 2.0),  # x half y half
        (5.0, 10.0, 1.0),  # x half y same
        (10.0, 5.0, 1.0),  # x same y half
    ],
)
def test_scale_factors(
    x: float,
    y: float,
    scale: float,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that getting scale factors for a given x and y coordinate"""
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_X", 10.0)
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_Y", 10.0)
    assert scale == svg2gcode.gcode_generator.get_scale(x, y)


def test_scale_factors_no_max_x(monkeypatch: pytest.MonkeyPatch):
    """Test that getting scale factors for a given x and y coordinate"""
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_X", None)
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_Y", 10.0)
    assert 1.0 == svg2gcode.gcode_generator.get_scale(10.0, 10.0)


def test_scale_factors_no_max_y(monkeypatch: pytest.MonkeyPatch):
    """Test that getting scale factors for a given x and y coordinate"""
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_X", 10.0)
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_Y", None)
    assert 1.0 == svg2gcode.gcode_generator.get_scale(10.0, 10.0)


def test_scale_factors_no_max_x_or_y(monkeypatch: pytest.MonkeyPatch):
    """Test that getting scale factors for a given x and y coordinate"""
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_X", None)
    monkeypatch.setattr("svg2gcode.gcode_generator.MAX_Y", None)
    assert 1.0 == svg2gcode.gcode_generator.get_scale(10.0, 10.0)
