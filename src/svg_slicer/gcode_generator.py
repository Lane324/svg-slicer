"""
Turns a SVG into gcode
"""

import math
import pathlib
from dataclasses import dataclass
from typing import Iterable, cast

import numpy as np
import scipy.optimize
import svgpathtools

from svg_slicer.slicing_options import SlicingOptions

HEADER = [
    "; Generated with svg-slicer",
    "",
    "",
]


# pylint: disable=too-few-public-methods
@dataclass
class GcodePoint:
    """Holds data about a point in gcode"""

    point: complex
    raised: bool

    def get_gcode(self, scale: float, options: SlicingOptions) -> list[str]:
        """
        Turns GcodePoint into gcode commands

        Args:
            scale: scale factor to apply to coordinates
            options: slicer options for generating gcode

        Returns:
            gcode commands
        """
        corrected_x = self.point.real * scale + options.start_point.real
        corrected_y = self.point.imag * scale + options.start_point.imag

        if corrected_x % 1 == 0:
            corrected_x = int(corrected_x)
        if corrected_y % 1 == 0:
            corrected_y = int(corrected_y)

        if self.raised:
            gcode = [
                *options.lift_gcode,
                f"G0 F{options.travel_feedrate}",
                f"G1 X{corrected_x} Y{corrected_y}",
                f"G0 F{options.normal_feedrate}",
                *options.unlift_gcode,
            ]
        else:
            gcode = [f"G1 X{corrected_x} Y{corrected_y}"]
        return gcode


class GcodeGenerator:
    """Generate gcode from an SVG file"""

    def __init__(self, slicing_options: SlicingOptions):
        """
        Creates GcodeGenerator

        Args:
            slicing_options: options for slicing
        """
        self.options = slicing_options
        self.largest_x: float = 0.0
        self.largest_y: float = 0.0
        self.gcode: list[str] = []
        self.points: list[GcodePoint] = []

    # pylint: disable=too-many-return-statements
    def _get_direction(self, start: complex, end: complex) -> float:
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

        return 0.0  # pragma no cover

    def _get_scale(self) -> float:
        """
        Gets scale factor to resize SVG to fit within max x and y

        Args:
            x: x value
            y: y value

        Returns:
            The smallest of the X or Y scale factor
        """

        x_scale: float = 1.0
        y_scale: float = 1.0

        if self.options.max_point:
            x_scale = self.options.max_point.real / self.largest_x
            y_scale = self.options.max_point.imag / self.largest_y

        return min(x_scale, y_scale)

    def _line_to_points(self, line: svgpathtools.Line) -> Iterable[complex]:
        """
        Converts a line to points

        Args:
            line: line to generate gcode for

        Returns:
            points calculated
        """

        self.largest_x = max(self.largest_x, line.start.real, line.end.real)
        self.largest_y = max(self.largest_y, line.start.imag, line.end.imag)

        return (line.start, line.end)

    def _arc_to_points(self, arc: svgpathtools.Arc) -> list[complex]:
        """
        Converts a arc to points

        Args:
            arc: line to generate gcode for

        Returns:
            points calculated
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

        xc, yc, theta1, theta2 = scipy.optimize.fsolve(ellipse_system, initial)

        xc = cast(int, xc)
        yc = cast(int, yc)

        center = xc + 1j * yc

        if theta2 < theta1:
            theta2 += 2 * np.pi

        arc_points: list[complex] = []
        for theta in np.linspace(theta1, theta2, self.options.curve_resolution):
            point: complex = center + arc.radius * np.exp(1j * theta) * exp_phi
            arc_points.append(point)
            self.largest_x = max(self.largest_x, point.real)
            self.largest_y = max(self.largest_y, point.imag)

        return arc_points

    def _quadricbezier_to_points(
        self, curve: svgpathtools.QuadraticBezier
    ) -> list[complex]:
        """
        Converts a quadratic bezier curve to gcode commands

        Args:
            curve: curve to generate gcode for

        Returns:
            points calculated
        """

        def get_point(t: float) -> complex:
            point: complex = complex(
                (1 - t) ** 2 * curve.start.real
                + 2 * (1 - t) * t * curve.control.real
                + t**2 * curve.end.real,
                (1 - t) ** 2 * curve.start.imag
                + 2 * (1 - t) * t * curve.control.imag
                + t**2 * curve.end.imag,
            )

            self.largest_x = max(self.largest_x, point.real)
            self.largest_y = max(self.largest_y, point.imag)
            return point

        points: list[complex] = [
            get_point(t) for t in np.linspace(0, 1, self.options.curve_resolution)
        ]

        return points

    def _cubicbezier_to_points(self, curve: svgpathtools.CubicBezier) -> list[complex]:
        """
        Converts a cubic bezier curve to points

        Args:
            curve: curve to generate gcode for

        Returns:
            points calculated
        """

        def get_point(t: float) -> complex:
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

            self.largest_x = max(self.largest_x, point.real)
            self.largest_y = max(self.largest_y, point.imag)
            return point

        points: list[complex] = [
            get_point(t) for t in np.linspace(0, 1, self.options.curve_resolution)
        ]

        return points

    def _extend_gcode_points(self, new_points: Iterable[complex], raised: bool):
        """
        Extends self.points from complex numbers

        Args:
            new_points: point to create
            raised: travel to next point raised
        """
        for point in new_points:
            self.points.append(GcodePoint(point=point, raised=raised))
            raised = False

    def _get_points(self, paths: tuple[list[svgpathtools.Path], ...]):
        """
        Gets all points on paths

        Args:
            paths: paths to get points for

        Returns:
            all_points: gcode points found
        """
        self.points.clear()
        new_points: Iterable[complex]
        prev_end: complex = complex(0, 0)

        raised = False
        for path in paths:
            for subpath in path:
                if prev_end != subpath.start:
                    raised = True

                if isinstance(subpath, svgpathtools.Line):
                    new_points = self._line_to_points(subpath)
                elif isinstance(subpath, svgpathtools.Arc):
                    new_points = self._arc_to_points(subpath)
                elif isinstance(subpath, svgpathtools.QuadraticBezier):
                    new_points = self._quadricbezier_to_points(subpath)
                elif isinstance(subpath, svgpathtools.CubicBezier):
                    new_points = self._cubicbezier_to_points(subpath)
                else:
                    continue

                self._extend_gcode_points(new_points, raised)
                raised = False
                prev_end = subpath.end

    def generate_gcode(self, svg_path: pathlib.Path):
        """
        Converts SVG to gcode

        Args:
            svg_path: path to SVG file
        """
        self.gcode.clear()

        parsed = svgpathtools.svg2paths(svg_path)
        paths: tuple[list[svgpathtools.Path]] = parsed[0]
        self._get_points(paths)

        self.gcode.extend(HEADER)
        self.gcode.extend(self.options.start_gcode)

        scale = self._get_scale()
        for point in self.points:
            self.gcode.extend(point.get_gcode(scale, self.options))

        self.gcode.extend(self.options.end_gcode)
