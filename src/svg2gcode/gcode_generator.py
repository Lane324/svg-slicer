"""
Turns a SVG into gcode
"""

import datetime
import math
import pathlib
import sys
from typing import cast

import numpy as np
import rich
import scipy.optimize
import svgpathtools

START_X = 10
START_Y = 10
START = complex(START_X, START_Y)
MAX_X = 100
MAX_Y = 50
NORMAL_FEEDRATE = 500
TRAVEL_FEEDRATE = 4000
CURVE_RESOLUTION = 50

HEADER = [
    f"; Generated with SVG gcode generator at {datetime.datetime.now().timestamp()}",
    "",
    "",
]
START_GCODE = [
    "; start",
    "M107 ; turn fan off",
    "G21 ; use millimeter",
    "G90 ; absolute coordinates",
    "M82 ; absolute E coordinates",
    "G92 E0 ; set E to 0",
    "G28 X Y Z ; home xyz axes",
    f"G1 F{NORMAL_FEEDRATE} ; set feedrate",
    "",
]
END_GCODE = [
    "; end",
    "DISPLAY",
]
LIFT_GCODE = "G1 Z10"
UNLIFT_GCODE = "G1 Z0"


class GcodePoint:
    def __init__(self, point: complex, raised: bool):
        """"""
        self.point: complex = point
        self.raised: bool = raised

    def get_gcode(self, scale: float) -> list[str]:
        """"""
        corrected_x = self.point.real * scale + START_X
        corrected_y = self.point.imag * scale + START_Y
        if self.raised:
            gcode = [
                LIFT_GCODE,
                f"G0 F{TRAVEL_FEEDRATE}",
                f"G1 X{corrected_x} Y{corrected_y}",
                f"G0 F{NORMAL_FEEDRATE}",
                UNLIFT_GCODE,
            ]
        else:
            gcode = [f"G1 X{corrected_x} Y{corrected_y}"]
        return gcode


# pylint: disable=too-many-return-statements
def get_direction(start: complex, end: complex) -> float:
    """
    Gets the direction between 2 points

    Args:
        start: start of segment
        end: end of segment

    Returns:
        direction from start to end in degrees
    """
    vector = end - start

    if vector.imag == 0 and vector.real == 0:
        return 0.0
    if vector.imag == 0 and vector.real > 0:
        return 0.0
    if vector.real == 0 and vector.imag > 0:
        return 90.0
    if vector.imag == 0 and vector.real < 0:
        return 180.0
    if vector.real == 0 and vector.imag < 0:
        return 270.0

    degrees = math.degrees(math.atan(vector.imag / vector.real))

    if vector.imag > 0:
        if vector.real > 0:
            return degrees  # quadrant 1
        return 180 + degrees  # quadrant 2

    if vector.imag < 0:
        if vector.real < 0:
            return 180 + degrees  # quadrant 3
        return 270 - degrees  # quadrant 4

    return 0.0


def get_scale(x: float, y: float) -> float:
    """
    Gets scale factor to resize SVG to fit within MAX_X and MAX_Y

    Args:
        x: x value
        y: y value

    Returns:
        The smallest of the X or Y scale factor
    """

    x_scale: float | None = None
    y_scale: float | None = None

    if MAX_X:
        x_scale = MAX_X / x
    if MAX_Y:
        y_scale = MAX_Y / y

    if x_scale and y_scale:
        return x_scale if x_scale < y_scale else y_scale
    if x_scale and not y_scale:
        return x_scale
    if not x_scale and y_scale:
        return y_scale

    return 1.0


def line_to_points(line: svgpathtools.Line) -> tuple[list[complex], float, float]:
    """
    Converts a line to gcode commands

    Args:
        line: line to generate gcode for

    Returns:
        points calculated and largest x coord and y coord
    """

    largest_x = line.start.real if line.start.real > line.end.real else line.end.real
    largest_y = line.start.imag if line.start.imag > line.end.imag else line.end.imag

    return (
        [
            line.start,
            line.end,
        ],
        largest_x,
        largest_y,
    )


def arc_to_points(arc: svgpathtools.Arc) -> tuple[list[complex], float, float]:
    """
    Converts a arc to gcode commands

    Args:
        arc: line to generate gcode for

    Returns:
        points calculated and largest x coord and y coord

    Raises:
        RuntimeError: could not determine the largest X or Y coordinate
    """

    exp_phi = np.exp(1j * np.radians(arc.rotation))

    def ellipse_system(variables):
        xc, yc, t1, t2 = variables
        c = xc + 1j * yc
        rhs1 = c + arc.radius * np.exp(1j * t1) * exp_phi
        rhs2 = c + arc.radius * np.exp(1j * t2) * exp_phi
        return [
            np.real(rhs1 - arc.start),
            np.imag(rhs1 - arc.start),
            np.real(rhs2 - arc.end),
            np.imag(rhs2 - arc.end),
        ]

    mid = (arc.start + arc.end) / 2
    initial = [mid.real, mid.imag, 0, np.pi / 2]

    solution = scipy.optimize.fsolve(ellipse_system, initial)
    xc, yc, theta1, theta2 = solution

    xc = cast(int, xc)
    yc = cast(int, yc)

    center = xc + 1j * yc

    if theta2 < theta1:
        theta2 += 2 * np.pi

    largest_x: float | None = None
    largest_y: float | None = None
    arc_points: list[complex] = []
    for theta in np.linspace(theta1, theta2, CURVE_RESOLUTION):
        point: complex = center + arc.radius * np.exp(1j * theta) * exp_phi
        arc_points.append(point)
        if not largest_x or point.real > largest_x:
            largest_x = point.real
        if not largest_y or point.real > largest_y:
            largest_y = point.real

    if not largest_x or not largest_y:
        raise RuntimeError("Could not find largest X or Y coordinate.")

    return (arc_points, largest_x, largest_y)


def quadricbezier_to_points(
    curve: svgpathtools.QuadraticBezier,
) -> tuple[list[complex], float, float]:
    """
    Converts a quadratic bezier curve to gcode commands

    Args:
        curve: curve to generate gcode for

    Returns:
        points calculated and largest x coord and y coord

    Raises:
        RuntimeError: could not determine the largest X or Y coordinate
    """

    largest_x: float | None = None
    largest_y: float | None = None

    def get_point(t: float) -> complex:
        nonlocal largest_x, largest_y
        point: complex = complex(
            (1 - t) ** 2 * curve.start.real
            + 2 * (1 - t) * t * curve.control.real
            + t**2 * curve.end.real,
            (1 - t) ** 2 * curve.start.imag
            + 2 * (1 - t) * t * curve.control.imag
            + t**2 * curve.end.imag,
        )

        if not largest_x or point.real > largest_x:
            largest_x = point.real
        if not largest_y or point.real > largest_y:
            largest_y = point.real
        return point

    points: list[complex] = [get_point(t) for t in np.linspace(0, 1, CURVE_RESOLUTION)]
    if not largest_x or not largest_y:
        raise RuntimeError("Could not find largest X or Y coordinate.")

    return (
        points,
        largest_x,
        largest_y,
    )


def cubicbezier_to_points(
    curve: svgpathtools.CubicBezier,
) -> tuple[list[complex], float, float]:
    """
    Converts a cubic bezier curve to gcode commands

    Args:
        curve: curve to generate gcode for

    Returns:
        points calculated and largest x coord and y coord

    Raises:
        RuntimeError: could not determine the largest X or Y coordinate
    """

    largest_x: float | None = None
    largest_y: float | None = None

    def get_point(t: float) -> complex:
        nonlocal largest_x, largest_y
        point: complex = complex(
            (1 - t) ** 3 * curve.start.real
            + 3 * (1 - t) ** 2 * t * curve.control1.real
            + 3 * (1 - t) * t**2 * curve.control2.real
            + t**3 * curve.end.real,
            (1 - t) ** 3 * curve.start.imag
            + 3 * (1 - t) ** 2 * t * curve.control1.imag
            + 3 * (1 - t) * t**2 * curve.control2.imag
            + t**3 * curve.end.imag,
        )

        if not largest_x or point.real > largest_x:
            largest_x = point.real
        if not largest_y or point.real > largest_y:
            largest_y = point.real
        return point

    points: list[complex] = [get_point(t) for t in np.linspace(0, 1, CURVE_RESOLUTION)]
    if not largest_x or not largest_y:
        raise RuntimeError("Could not find largest X or Y coordinate.")

    return (
        points,
        largest_x,
        largest_y,
    )


def make_gcode_points(points: list[complex], raised: bool) -> list[GcodePoint]:
    """
    Constructs GcodePoints from complex numbers

    Args:
        points: point to create
        raised: travel to next point raised

    Returns:
        gcode_points: GcodePoints
    """
    gcode_points: list[GcodePoint] = []
    for point in points:
        gcode_points.append(GcodePoint(point, raised))
        raised = False
    return gcode_points


def get_points(
    paths: tuple[list[svgpathtools.Path]],
) -> tuple[list[GcodePoint], float, float]:
    """
    Gets all points on paths

    Args:
        paths: paths to get points for

    Returns:
        all_points: gcode points found
    """
    largest_x: float = 0.0
    largest_y: float = 0.0
    all_points: list[GcodePoint] = []
    new_points: list[complex]
    prev_end: complex = complex(0, 0)

    raised = False
    for path in paths:
        for subpath in path:
            if prev_end != subpath.start:
                raised = True

            if isinstance(subpath, svgpathtools.Line):
                new_points, new_largest_x, new_largest_y = line_to_points(subpath)
            elif isinstance(subpath, svgpathtools.Arc):
                new_points, new_largest_x, new_largest_y = arc_to_points(subpath)
            elif isinstance(subpath, svgpathtools.QuadraticBezier):
                new_points, new_largest_x, new_largest_y = quadricbezier_to_points(
                    subpath
                )
            elif isinstance(subpath, svgpathtools.CubicBezier):
                new_points, new_largest_x, new_largest_y = cubicbezier_to_points(
                    subpath
                )
            else:
                continue

            if new_largest_x > largest_x:
                largest_x = new_largest_x
            if new_largest_y > largest_y:
                largest_y = new_largest_y

            all_points.extend(make_gcode_points(new_points, raised))
            raised = False
            prev_end = subpath.end

    return (all_points, largest_x, largest_y)


def generate_gcode(svg_path: pathlib.Path) -> tuple[list[str], list[GcodePoint]]:
    """
    Converts SVG to gcode

    Args:
        svg_path: path to SVG file
    """

    parsed = svgpathtools.svg2paths(svg_path)
    paths: tuple[list[svgpathtools.Path]] = parsed[0]

    gcode: list[str] = []
    gcode.extend(HEADER)
    gcode.extend(START_GCODE)

    points, largest_x, largest_y = get_points(paths)

    scale = get_scale(largest_x, largest_y)
    for point in points:
        gcode.extend(point.get_gcode(scale))

    gcode.extend(END_GCODE)

    return (gcode, points)


def save_gcode(path: pathlib.Path, gcode: list[str]):
    """"""
    with path.open("w") as f:
        for line in gcode:
            f.write(line + "\n")
    rich.print(f"Created gcode file at [yellow]{path}[/yellow]")


def main():
    """
    Main entry point
    """
    svg_path = pathlib.Path(sys.argv[1])
    gcode, points = generate_gcode(svg_path)
    gcode_path = pathlib.Path.cwd() / f"{svg_path.stem}.gcode"
    save_gcode(gcode_path, gcode)
