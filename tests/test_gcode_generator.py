"""
Tests svg_slicer.gcode_generator
"""

import pathlib
from unittest import mock

import pytest
import svgpathtools

from svg_slicer import gcode_generator, slicing_options


# region Mocks
@pytest.fixture()
def mock_slicing_options() -> slicing_options.SlicingOptions:
    return slicing_options.SlicingOptions(
        start_point=complex(0, 0),
        max_point=complex(10, 10),
        normal_feedrate=500,
        travel_feedrate=1000,
        curve_resolution=10,
        start_gcode=["; start"],
        end_gcode=["; end"],
        lift_gcode=["G1 Z10"],
        unlift_gcode=["G1 Z0"],
    )


@pytest.fixture()
def mock_generator(
    mock_slicing_options: slicing_options.SlicingOptions,
) -> gcode_generator.GcodeGenerator:
    """"""
    return gcode_generator.GcodeGenerator(mock_slicing_options)


# endregion
# region GcodePoint.get_gcode


def test_gcode_point_correctly_creates_gcode(
    mock_slicing_options: slicing_options.SlicingOptions,
):
    """Tests that a GcodePoint creates correct gcode commands when not raised"""
    point = complex(1, 1)
    raised = False
    gcode_point = gcode_generator.GcodePoint(point=point, raised=raised)

    gcode = gcode_point.get_gcode(scale=1.0, options=mock_slicing_options)

    assert gcode == [f"G1 X{int(point.real)} Y{int(point.imag)}"]


def test_gcode_point_correctly_creates_gcode_floating_points(
    mock_slicing_options: slicing_options.SlicingOptions,
):
    """Tests that a GcodePoint creates correct gcode commands when not raised"""
    point = complex(1.1, 1.2)
    raised = False
    gcode_point = gcode_generator.GcodePoint(point=point, raised=raised)

    gcode = gcode_point.get_gcode(scale=1.0, options=mock_slicing_options)

    assert gcode == [f"G1 X{point.real} Y{point.imag}"]


def test_gcode_point_correctly_creates_gcode_raised(
    mock_slicing_options: slicing_options.SlicingOptions,
):
    """Tests that a GcodePoint creates correct gcode commands when raised"""
    point = complex(1, 1)
    raised = True
    gcode_point = gcode_generator.GcodePoint(point=point, raised=raised)

    gcode = gcode_point.get_gcode(scale=1.0, options=mock_slicing_options)

    assert gcode == [
        *mock_slicing_options.lift_gcode,
        f"G0 F{mock_slicing_options.travel_feedrate}",
        f"G1 X{int(point.real)} Y{int(point.imag)}",
        f"G0 F{mock_slicing_options.normal_feedrate}",
        *mock_slicing_options.unlift_gcode,
    ]


# endregion
# region GcodeGenerator.__init__


def test_gcode_generator_inits(mock_slicing_options: slicing_options.SlicingOptions):
    """Test that GcodeGenerator inits without error"""
    gcode_generator.GcodeGenerator(mock_slicing_options)


# endregion
# region GcodeGenerator._get_direction


@pytest.mark.parametrize(
    "start,end,expected_direction",
    [
        (0 + 0j, 0 + 0j, 0.0),  # zero length vector
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
    mock_slicing_options: slicing_options.SlicingOptions,
    start: complex,
    end: complex,
    expected_direction: float,
):
    """Test that getting the direction between 2 points returns the correct degrees"""
    generator = gcode_generator.GcodeGenerator(mock_slicing_options)
    assert generator._get_direction(start, end) == expected_direction


# endregion
# region GcodeGenerator._get_scale


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
    mock_slicing_options: slicing_options.SlicingOptions,
    x: float,
    y: float,
    scale: float,
):
    """Test that getting scale factors for a given x and y coordinate"""
    generator = gcode_generator.GcodeGenerator(mock_slicing_options)
    generator.largest_x = x
    generator.largest_y = y
    assert scale == generator._get_scale()


def test_scale_factors_no_max_point(
    mock_slicing_options: slicing_options.SlicingOptions,
):
    """Test that getting scale factors for a given x and y coordinate"""
    generator = gcode_generator.GcodeGenerator(mock_slicing_options)
    generator.options.max_point = None
    assert 1.0 == generator._get_scale()


# endregion
# region GcodeGenerator._line_to_points


def test_converting_line_to_points(mock_generator: gcode_generator.GcodeGenerator):
    """Tests that a line can be converted into points and the largest xy is set"""
    start = complex(0, 0)
    end = complex(100, 200)
    line = svgpathtools.Line(start, end)

    assert mock_generator._line_to_points(line) == (start, end)
    assert mock_generator.largest_x == end.real
    assert mock_generator.largest_y == end.imag


# endregion
# region GcodeGenerator._arc_to_points


def test_converting_arc_to_points(mock_generator: gcode_generator.GcodeGenerator):
    """Tests that a arc can be converted into points and the largest xy is set"""
    arc = svgpathtools.Arc(
        start=complex(0, 0),
        radius=complex(1, 1),
        rotation=0.0,
        large_arc=True,
        sweep=False,
        end=complex(10, 10),
    )
    resolution = 9

    mock_generator.options.curve_resolution = resolution

    assert len(mock_generator._arc_to_points(arc)) == resolution


def test_converting_arc_to_points_positive_to_negative(
    mock_slicing_options: slicing_options.SlicingOptions,
):
    """Tests that a arc can be converted into points and the largest xy is set"""
    arc = svgpathtools.Arc(
        start=complex(0, 10),
        radius=complex(1, 1),
        rotation=0.0,
        large_arc=True,
        sweep=False,
        end=complex(20, 10),
    )
    resolution = 9

    mock_slicing_options.curve_resolution = resolution
    generator = gcode_generator.GcodeGenerator(mock_slicing_options)

    # correct number of points are generated not that math is correct
    assert len(generator._arc_to_points(arc)) == resolution


# endregion
# region GcodeGenerator._quadricbezier_to_points


def test_converting_quadricbezier_to_points(
    mock_generator: gcode_generator.GcodeGenerator,
):
    """Tests that a quadricbezier can be converted into points and the largest xy is set"""

    curve = svgpathtools.QuadraticBezier(
        start=complex(0, 0), control=complex(1, 1), end=complex(2, 3)
    )
    resolution = 9

    mock_generator.options.curve_resolution = resolution

    # correct number of points are generated not that math is correct
    assert len(mock_generator._quadricbezier_to_points(curve)) == resolution

    assert mock_generator.largest_x == 2
    assert mock_generator.largest_y == 3


# endregion
# region GcodeGenerator._cubicbezier_to_points


def test_converting_cubicbezier_to_points(
    mock_generator: gcode_generator.GcodeGenerator,
):
    """Tests that a cubicbezier can be converted into points and the largest xy is set"""

    curve = svgpathtools.CubicBezier(
        start=complex(0, 0),
        control1=complex(1, 1),
        control2=complex(2, 2),
        end=complex(3, 4),
    )
    resolution = 9

    mock_generator.options.curve_resolution = resolution

    # correct number of points are generated not that math is correct
    assert len(mock_generator._cubicbezier_to_points(curve)) == resolution

    assert mock_generator.largest_x == 3
    assert mock_generator.largest_y == 4


# endregion
# region GcodeGenerator._extend_gcode_points


def test_extend_points_with_complex_numbers(
    mock_generator: gcode_generator.GcodeGenerator,
):
    """Tests that ading more complex numbers to self.points adds them with as GcodePoints"""
    point1 = complex(1, 1)
    point2 = complex(2, 2)
    point3 = complex(3, 3)
    new_points = (point1, point2, point3)

    mock_generator._extend_gcode_points(new_points=new_points, raised=True)

    assert mock_generator.points == [
        gcode_generator.GcodePoint(point1, True),
        gcode_generator.GcodePoint(point2, False),
        gcode_generator.GcodePoint(point3, False),
    ]


# endregion
# region GcodeGenerator._get_points


def test_getting_points_from_multiple_curves(
    mock_generator: gcode_generator.GcodeGenerator,
    monkeypatch: pytest.MonkeyPatch,
):
    """Tests that getting points from multiple curve types"""

    line = svgpathtools.Line(complex(0, 0), complex(10, 20))
    arc = svgpathtools.Arc(
        start=complex(10, 20),
        radius=complex(1, 1),
        rotation=0.0,
        large_arc=True,
        sweep=False,
        end=complex(20, 30),
    )
    quadricbezier_curve = svgpathtools.QuadraticBezier(
        start=complex(20, 30), control=complex(1, 1), end=complex(30, 40)
    )
    cubicbezier_curve = svgpathtools.CubicBezier(
        start=complex(40, 50),
        control1=complex(1, 1),
        control2=complex(2, 2),
        end=complex(50, 60),  # make it raise
    )
    paths = ([line, arc], [quadricbezier_curve, cubicbezier_curve, svgpathtools.Path()])

    mock_line_to_points = mock.create_autospec(
        gcode_generator.GcodeGenerator._line_to_points, return_value=(complex(1, 1),)
    )
    mock_arc_to_points = mock.create_autospec(
        gcode_generator.GcodeGenerator._arc_to_points,
        return_value=(complex(1, 1), complex(2, 2)),
    )
    mock_quadricbezier_to_points = mock.create_autospec(
        gcode_generator.GcodeGenerator._quadricbezier_to_points,
        return_value=(complex(1, 1), complex(2, 2), complex(3, 3)),
    )
    mock_cubicbezier_to_points = mock.create_autospec(
        gcode_generator.GcodeGenerator._cubicbezier_to_points,
        return_value=(complex(1, 1), complex(2, 2), complex(4, 4), complex(5, 5)),
    )

    monkeypatch.setattr(
        gcode_generator.GcodeGenerator, "_line_to_points", mock_line_to_points
    )
    monkeypatch.setattr(
        gcode_generator.GcodeGenerator, "_arc_to_points", mock_arc_to_points
    )
    monkeypatch.setattr(
        gcode_generator.GcodeGenerator,
        "_quadricbezier_to_points",
        mock_quadricbezier_to_points,
    )
    monkeypatch.setattr(
        gcode_generator.GcodeGenerator,
        "_cubicbezier_to_points",
        mock_cubicbezier_to_points,
    )

    mock_generator._get_points(paths)

    assert len(mock_generator.points) == 10


# endregion
# region GcodeGenerator.generate_gcode


def test_generating_gcode(
    mock_generator: gcode_generator.GcodeGenerator,
    monkeypatch: pytest.MonkeyPatch,
):
    """Tests that generating gcode makes correct gcode commands"""

    svg_path = pathlib.Path("image.svg")

    points: list[gcode_generator.GcodePoint] = [
        gcode_generator.GcodePoint(complex(1, 1), True),
        gcode_generator.GcodePoint(complex(1, 2), False),
        gcode_generator.GcodePoint(complex(2, 2), False),
        gcode_generator.GcodePoint(complex(2, 1), False),
        gcode_generator.GcodePoint(complex(1, 1), False),
    ]
    scale = 1.0

    mock_svg2paths = mock.create_autospec(
        svgpathtools.svg2paths, return_value=(None, None)
    )
    monkeypatch.setattr(gcode_generator.svgpathtools, "svg2paths", mock_svg2paths)

    mock_get_points = mock.create_autospec(gcode_generator.GcodeGenerator._get_points)
    monkeypatch.setattr(gcode_generator.GcodeGenerator, "_get_points", mock_get_points)
    mock_get_scale = mock.create_autospec(
        gcode_generator.GcodeGenerator._get_scale, return_value=scale
    )
    monkeypatch.setattr(gcode_generator.GcodeGenerator, "_get_scale", mock_get_scale)

    mock_generator.points = points
    mock_generator.generate_gcode(svg_path)

    expected_gcode = [
        *gcode_generator.HEADER,
        *mock_generator.options.start_gcode,
        *[c for p in points for c in p.get_gcode(scale, mock_generator.options)],
        *mock_generator.options.end_gcode,
    ]

    assert mock_generator.gcode == expected_gcode


# endregion
