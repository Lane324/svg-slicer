import pathlib
import re

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

GCODE_COORD_REGEX = re.compile(r"([XYZ])([-+]?\d*\.?\d+)")


class GcodeViewer(QWidget):
    # class GcodeViewer:
    def __init__(self):
        super().__init__()
        self.gcode_file: pathlib.Path | None = None
        self.coordinate_points: tuple[list[float], list[float], list[float]] = (
            [],
            [],
            [],
        )

        self.fig = Figure((5, 3))
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.fig.set_canvas(self.canvas)
        self._ax = self.canvas.figure.add_subplot(projection="3d")
        self._ax.set_xlabel("X")
        self._ax.set_ylabel("Y")
        self._ax.set_zlabel("Z")

        self._ax.view_init(30, 30)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.canvas)
        self.setLayout(main_layout)

    def load_file(self, file: pathlib.Path):
        self.gcode_file = file

        with file.open() as f:
            gcode_data = f.read().splitlines()

        self.load_gcode(gcode_data)

    def load_gcode(self, gcode: list[str]):
        prev_x = 0.0
        prev_y = 0.0
        prev_z = 0.0
        self.coordinate_points = ([], [], [])
        for line in gcode:
            extracted_point = self._extract_point(line)
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

    def _extract_point(self, gcode_command: str) -> (
        tuple[
            float | None,
            float | None,
            float | None,
        ]
        | None
    ):
        if not gcode_command.startswith("G0") and not gcode_command.startswith("G1"):
            return None

        coords = dict(GCODE_COORD_REGEX.findall(gcode_command))
        if not coords:
            return None

        coords = {axis: float(value) for axis, value in coords.items()}
        x = coords.get("X")
        y = coords.get("Y")
        z = coords.get("Z")
        if x is not None and y is not None and z is not None:
            return None

        return (x, y, z)

    def plot_gcode(self):
        self._ax.clear()
        self._ax.plot3D(*self.coordinate_points, "green")
        self.canvas.draw()
