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

START_X = 100
START_Y = 70
MAX_X = 100
MAX_Y = 200
NORMAL_FEEDRATE = 500
TRAVEL_FEEDRATE = 4000
CURVE_RESOLUTION = 50
OVER_CUT = 0.2

HEADER = (
    f"; Generated with SVG gcode generator at {datetime.datetime.now().timestamp()}\n\n"
)
START_GCODE = [
    "; start\n",
    "M107 ; turn fan off\n",
    "G21 ; use millimeter\n",
    "G90 ; absolute coordinates\n",
    "M82 ; absolute E coordinates\n",
    "G92 E0 ; set E to 0\n",
    "G28 X Y Z ; home xyz axes\n",
    f"G1 F{NORMAL_FEEDRATE} ; set feedrate\n",
    "\n\n",
]
END_GCODE = [
    "; end\n",
    "DISPLAY\n",
]
LIFT_GCODE = "G1 Z10\n"
UNLIFT_GCODE = "G1 Z0\n"


# pylint: disable=too-many-return-statements
def get_direction(start: complex, end: complex) -> float:
    """
    Gets the direction between 2 points

    Args:
        start: start of segment
        end: end of segment

    Returns:
        direction from start to end in degrees

    Raises:
        failed to calculate a valid direction
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

    raise RuntimeError("Invalid degree calculated")


def get_scale(paths: tuple[list[svgpathtools.Path]]) -> tuple[float, float]:
    """
    Gets scale factor to resize SVG to fit within MAX_X and MAX_Y

    Args:
        paths: paths inside SVG file

    Returns:
        X and Y scale factor
    """
    if not MAX_X and not MAX_Y:
        return (1.0, 1.0)

    biggest_x: float = 0.0
    biggest_y: float = 0.0
    for path in paths:
        for line in path:
            for coord in (line.start, line.end):
                biggest_x = max(biggest_x, coord.real)
                biggest_y = max(biggest_y, coord.imag)

    if MAX_X and MAX_Y:
        return (MAX_X / biggest_x, MAX_Y / biggest_y)
    if MAX_X and not MAX_Y:
        return (MAX_X / biggest_x, 1)
    if not MAX_X and MAX_Y:
        return (1, MAX_Y / biggest_y)

    raise RuntimeError("Could not calculate scale")


def get_overcut(start_point: complex, current_point: complex) -> complex:
    """
    Draws straight line between 2 points with overlap to account for blade offset

    Args:
        start_point: point to connect to
        current_point: point to connect from
    """

    distance = math.dist(
        (current_point.real, current_point.imag), (start_point.real, start_point.imag)
    )

    vector: complex = (start_point - current_point) / distance

    return current_point + distance * vector


def line_to_gcode(line: svgpathtools.Line, scale: float, raised: bool) -> list[str]:
    """
    Converts a line to gcode commands

    Args:
        line: line to generate gcode for
        scale: scale factor
        raised: if the Z axis is raised or lowered

    Returns:
        gcode command generated
    """
    gcode = []
    if raised:
        gcode.append(LIFT_GCODE)
        gcode.append(f"G0 F{TRAVEL_FEEDRATE}\n")
        gcode.append(
            f"G1 X{START_X + line.start.real * scale} Y{START_Y + line.start.imag * scale}\n"
        )
        gcode.append(f"G0 F{NORMAL_FEEDRATE}\n")
        gcode.append(UNLIFT_GCODE)
    gcode.append(
        f"G1 X{START_X + line.end.real * scale} Y{START_Y + line.end.imag * scale}\n"
    )
    return gcode


def arc_to_gcode(arc: svgpathtools.Arc, scale: float, raised: bool) -> tuple[complex]:
    """
    Converts a arc to gcode commands

    Args:
        arc: line to generate gcode for
        scale: scale factor
        raised: if the Z axis is raised or lowered

    Returns:
        gcode command generated
    """

    # Function to solve for center and angles
    def ellipse_system(variables):
        xc, yc, t1, t2 = variables
        c = xc + 1j * yc
        exp_phi = np.exp(1j * np.radians(arc.rotation))
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
    arc_points: np.ndarray = center + arc.radius * np.exp(
        1j * np.linspace(theta1, theta2, CURVE_RESOLUTION)
    ) * np.exp(1j * np.radians(arc.rotation))

    gcode = []

    for point in arc_points:
        if raised:
            gcode.append(LIFT_GCODE)
            gcode.append(f"G0 F{TRAVEL_FEEDRATE}\n")
            gcode.append(
                f"G1 X{START_X + point.real * scale} Y{START_Y + point.imag * scale}\n"
            )
            gcode.append(f"G0 F{NORMAL_FEEDRATE}\n")
            gcode.append(UNLIFT_GCODE)
            raised = False
        gcode.append(
            f"G1 X{START_X + point.real * scale} Y{START_Y + point.imag * scale}\n"
        )
    return gcode


def quadricbezier_to_gcode(
    curve: svgpathtools.QuadraticBezier, scale: float, raised: bool
) -> list[str]:
    """
    Converts a quadratic bezier curve to gcode commands

    Args:
        curve: curve to generate gcode for
        scale: scale factor
        raised: if the Z axis is raised or lowered

    Returns:
        gcode command generated
    """
    gcode = []

    for t in np.linspace(0, 1, CURVE_RESOLUTION):
        x: float = (
            (1 - t) ** 2 * curve.start.real
            + 2 * (1 - t) * t * curve.control.real
            + t**2 * curve.end.real
        )
        y: float = (
            (1 - t) ** 2 * curve.start.imag
            + 2 * (1 - t) * t * curve.control.imag
            + t**2 * curve.end.imag
        )
        if raised:
            gcode.append(LIFT_GCODE)
            gcode.append(f"G0 F{TRAVEL_FEEDRATE}\n")
            gcode.append(f"G1 X{START_X + x * scale} Y{START_Y + y * scale}\n")
            gcode.append(f"G0 F{NORMAL_FEEDRATE}\n")
            gcode.append(UNLIFT_GCODE)
            raised = False
        gcode.append(f"G1 X{START_X + x * scale} Y{START_Y + y * scale}\n")
    return gcode


def cubicbezier_to_gcode(
    curve: svgpathtools.CubicBezier, scale: float, raised: bool
) -> list[str]:
    """
    Converts a cubic bezier curve to gcode commands

    Args:
        curve: curve to generate gcode for
        scale: scale factor
        raised: if the Z axis is raised or lowered

    Returns:
        gcode command generated
    """
    gcode = []

    for t in np.linspace(0, 1, CURVE_RESOLUTION):
        x: float = (
            (1 - t) ** 3 * curve.start.real
            + 3 * (1 - t) ** 2 * t * curve.control1.real
            + 3 * (1 - t) * t**2 * curve.control2.real
            + t**3 * curve.end.real
        )
        y: float = (
            (1 - t) ** 3 * curve.start.imag
            + 3 * (1 - t) ** 2 * t * curve.control1.imag
            + 3 * (1 - t) * t**2 * curve.control2.imag
            + t**3 * curve.end.imag
        )

        if raised:
            gcode.append(LIFT_GCODE)
            gcode.append(f"G0 F{TRAVEL_FEEDRATE}\n")
            gcode.append(f"G1 X{START_X + x * scale} Y{START_Y + y * scale}\n")
            gcode.append(f"G0 F{NORMAL_FEEDRATE}\n")
            gcode.append(UNLIFT_GCODE)
            raised = False
        gcode.append(f"G1 X{START_X + x * scale} Y{START_Y + y * scale}\n")
    return gcode


def generate_gcode(svg_path: pathlib.Path):
    """
    Converts SVG to gcode

    Args:
        svg_path: path to SVG file
    """
    gcode: list[str] = [HEADER]
    gcode.extend(START_GCODE)

    parsed = svgpathtools.svg2paths(svg_path)
    paths: tuple[list[svgpathtools.Path]] = parsed[0]
    x_scale, y_scale = get_scale(paths)
    scale = x_scale if x_scale < y_scale else y_scale

    start_point = None
    prev_end: complex = complex(0, 0)
    raised = False
    for path in paths:
        for subpath in path:
            if prev_end != subpath.start:
                raised = True
            if isinstance(subpath, svgpathtools.Line):
                gcode.extend(line_to_gcode(subpath, scale, raised))
            elif isinstance(subpath, svgpathtools.Arc):
                gcode.extend(arc_to_gcode(subpath, scale, raised))
            elif isinstance(subpath, svgpathtools.QuadraticBezier):
                gcode.extend(quadricbezier_to_gcode(subpath, scale, raised))
            elif isinstance(subpath, svgpathtools.CubicBezier):
                gcode.extend(cubicbezier_to_gcode(subpath, scale, raised))

            raised = False
            prev_end = subpath.end

    gcode.extend(END_GCODE)

    gcode_path = pathlib.Path.cwd() / f"{svg_path.stem}.gcode"
    with gcode_path.open("w") as f:
        f.writelines(gcode)
    rich.print(f"Created gcode file at [yellow]{gcode_path}[/yellow]")


def main():
    """
    Main entry point
    """
    generate_gcode(pathlib.Path(sys.argv[1]))


if __name__ == "__main__":
    main()
