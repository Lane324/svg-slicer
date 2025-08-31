"""gcode viewer widget"""

import pathlib
import re
from typing import cast

from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import axis3d

# pylint: disable=no-name-in-module
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

GCODE_G0_G1_REGEX = re.compile(r"([XYZ])([-+]?\d*\.?\d+)")
GCODE_G28_REGEX = re.compile(r"([XYZ])")
HOME_VIEW = (45, 180 + 45)
TOP_DOWN_VIEW = (90, 270)


class GcodeViewer(QWidget):
    """Widget to view gcode files"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        super().__init__()
        self.gcode_file: pathlib.Path | None = None
        self.coordinate_points: tuple[list[float], list[float], list[float]] = (
            [],
            [],
            [],
        )

        self._create_figure()
        self._create_widgets()
        self._create_layouts()

        self.canvas.mpl_connect("scroll_event", self._zoom)

    def _create_figure(self):
        """Creates matplotlib figure for gcode plotting"""
        self.fig = Figure((5, 3))
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.fig.set_canvas(self.canvas)
        self._ax = self.canvas.figure.add_subplot(projection="3d")
        self._ax.view_init(*HOME_VIEW)
        self._ax.set_xlabel("X")
        self._ax.set_ylabel("Y")
        self._ax.set_zlabel("Z")
        self._ax.xaxis = cast(axis3d.XAxis, self._ax.xaxis)
        self._ax.yaxis = cast(axis3d.YAxis, self._ax.yaxis)  # type: ignore
        self._ax.xaxis.line.set_color("red")
        self._ax.yaxis.line.set_color("green")  # type: ignore
        self._ax.zaxis.line.set_color("blue")

    def _create_widgets(self):
        """Creates all subwidgets"""

        self.views_group = QGroupBox("Views")
        self.home_view_button = QPushButton("Home")
        self.top_view_button = QPushButton("Top")

        self.gcode_text_viewer = QTextEdit()
        self.gcode_text_viewer.setReadOnly(True)
        self._connect_widgets()

    def _connect_widgets(self):
        """Connects widgets to their slots"""
        self.home_view_button.clicked.connect(self.change_to_home_view)
        self.top_view_button.clicked.connect(self.change_to_top_view)

    def _create_layouts(self):
        """Creates and congiures all layouts in widget"""
        self.main_layout = QHBoxLayout()
        self.plot_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.button_layout.addWidget(self.home_view_button)
        self.button_layout.addWidget(self.top_view_button)
        self.views_group.setLayout(self.button_layout)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.views_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )

        self.plot_layout.addWidget(self.views_group)
        self.plot_layout.addWidget(self.canvas)
        self.main_layout.addLayout(self.plot_layout, 3)
        self.main_layout.addWidget(self.gcode_text_viewer, 1)
        self.setLayout(self.main_layout)

    def _zoom(self, event: MouseEvent):
        """
        Allows the scroll wheel to zoom in on the plot

        Args:
            event: scroll wheel was moved
        """
        scale_factor = 1.1 if event.button == "up" else 0.9  # set zoom resolution

        # change X, Y, and Z limit based on their current limits with a scale factor
        self._ax.set_xlim(
            self._ax.get_xlim()[0] * scale_factor, self._ax.get_xlim()[1] * scale_factor
        )
        self._ax.set_ylim(
            self._ax.get_ylim()[0] * scale_factor, self._ax.get_ylim()[1] * scale_factor
        )
        self._ax.set_zlim(
            self._ax.get_zlim()[0] * scale_factor, self._ax.get_zlim()[1] * scale_factor
        )

        self.canvas.draw_idle()

    def load_file(self, file: pathlib.Path):
        """
        Loads gcode from a file

        Args:
            file: path to gcode file
        """
        self.gcode_file = file

        with file.open() as f:
            gcode_data = f.read().splitlines()

        self.load_gcode(gcode_data)

    def load_gcode(self, gcode: list[str]):
        """
        Loads gcode from a list of strings

        Args:
            gcode: gcode to plot
        """
        prev_x = 0.0
        prev_y = 0.0
        prev_z = 0.0
        self.coordinate_points = ([], [], [])
        for line in gcode:
            extracted_point = self._process_gcode_command(line)
            if not extracted_point:
                continue
            x, y, z = extracted_point
            if x is not None:
                self.coordinate_points[0].append(x)
                prev_x = x
            else:
                self.coordinate_points[0].append(prev_x)
            if y is not None:
                self.coordinate_points[1].append(y)
                prev_y = y
            else:
                self.coordinate_points[1].append(prev_y)
            if z is not None:
                self.coordinate_points[2].append(z)
                prev_z = z
            else:
                self.coordinate_points[2].append(prev_z)

        self.plot_gcode()
        self.gcode_text_viewer.setPlainText("\n".join(gcode))

    def _process_gcode_command(self, command: str) -> (
        tuple[
            float | None,
            float | None,
            float | None,
        ]
        | None
    ):
        """
        Processes a gcode command

        Args:
            command: command to process

        Returns:
            next coordinate to move to
        """
        if command.startswith("G0") or command.startswith("G1"):
            return self._process_g0_g1(command)
        if command.startswith("G28"):
            return self._process_g28(command)
        return None

    def _process_g0_g1(self, command: str) -> (
        tuple[
            float | None,
            float | None,
            float | None,
        ]
        | None
    ):
        """
        Strips the coordinates from a G0 or G1 command

        Args:
            command: G0 or G1 command

        Returns:
            stripped coordinates
        """
        coords = dict(GCODE_G0_G1_REGEX.findall(command))
        if not coords:
            return None

        coords = {axis: float(value) for axis, value in coords.items()}
        x = coords.get("X")
        y = coords.get("Y")
        z = coords.get("Z")
        if x is not None and y is not None and z is not None:
            return None

        return (x, y, z)

    def _process_g28(self, command: str) -> (
        tuple[
            float | None,
            float | None,
            float | None,
        ]
        | None
    ):
        """
        Processes a G28 command

        Args:
            command: G28 command

        Returns:
            coordinates after G28 command is executed
        """
        homed_axes = GCODE_G28_REGEX.findall(command)

        x: float | None = None
        y: float | None = None
        z: float | None = None

        if not homed_axes:
            x = 0.0
            y = 0.0
            z = 0.0
        if "X" in homed_axes:
            x = 0.0
        if "Y" in homed_axes:
            y = 0.0
        if "Z" in homed_axes:
            z = 0.0

        return (x, y, z)

    def plot_gcode(self):
        """Plots known coordinate points"""
        self._ax.cla()
        self._ax.plot3D(*self.coordinate_points, "green", linewidth=0.5)
        self.canvas.draw()

    @Slot()
    def change_to_home_view(self):
        """Changes view of 3D plot to home view"""
        self._ax.view_init(*HOME_VIEW)
        self.canvas.draw()

    @Slot()
    def change_to_top_view(self):
        """Changes view of 3D plot to top down view"""
        self._ax.view_init(*TOP_DOWN_VIEW)
        self.canvas.draw()
