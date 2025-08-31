"""
Holds slicing options
"""

import pathlib
import tomllib
from dataclasses import dataclass

import tomli_w

# pylint: disable=no-name-in-module
from PySide6.QtCore import QFile, QSaveFile, QTextStream, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

DEFAULT_TOML_PATH = (
    pathlib.Path().home() / "AppData" / "Roaming" / "svg2gcode" / "svg2gcode.toml"
)

DEFAULT_START_POINT = complex(0, 0)
DEFAULT_MAX_POINT = None
DEFAULT_NORMAL_FEEDRATE = 500
DEFAULT_TRAVEL_FEEDRATE = 4000
DEFAULT_CURVE_RESOLUTION = 20
DEFAULT_START_GCODE = [
    "; start",
    "M107 ; turn fan off",
    "G21 ; use millimeter",
    "G90 ; absolute coordinates",
    "M82 ; absolute E coordinates",
    "G92 E0 ; set E to 0",
    "G28 ; home xyz axes",
    "G1 F500 ; set feedrate",
    "",
]
DEFAULT_END_GCODE = ["; end"]
DEFAULT_LIFT_GCODE = ["G1 Z10"]
DEFAULT_UNLIFT_GCODE = ["G1 Z0"]


@dataclass
class SlicingOptions:
    """Holds slicing options"""

    start_point: complex
    max_point: complex | None
    normal_feedrate: int
    travel_feedrate: int
    curve_resolution: int
    start_gcode: list[str]
    end_gcode: list[str]
    lift_gcode: list[str]
    unlift_gcode: list[str]

    def get_dict(self) -> dict:
        """"""
        return {
            "machine": {
                "normal_feedrate": self.normal_feedrate,
                "travel_feedrate": self.travel_feedrate,
            },
            "gcode": {
                "start": self.start_gcode,
                "end": self.end_gcode,
                "lift": self.lift_gcode,
                "unlift": self.unlift_gcode,
            },
            "point": {
                "start_x": self.start_point.real,
                "start_y": self.start_point.imag,
                "max_x": self.max_point.real if self.max_point else None,
                "max_y": self.max_point.imag if self.max_point else None,
            },
        }


class SlicingOptionsWiget(QWidget):
    def __init__(
        self,
        options: SlicingOptions | None = None,
        options_file: pathlib.Path | None = None,
    ):
        super().__init__()

        self._create_widgets()
        self._create_layouts()

        if options:
            self.options: SlicingOptions = options
        elif options_file:
            self.load_options(options_file)
        else:
            self.load_default()

    def _create_widgets(self):

        self.status_bar = QStatusBar()

        # Input boxes
        self.start_x_input = QTextEdit()
        self.start_y_input = QTextEdit()
        self.max_x_input = QTextEdit()
        self.max_y_input = QTextEdit()
        self.normal_feedrate_input = QTextEdit()
        self.travel_feedrate_input = QTextEdit()
        self.curve_resolution_input = QTextEdit()
        self.start_gcode_input = QTextEdit()
        self.end_gcode_input = QTextEdit()
        self.lift_gcode_input = QTextEdit()
        self.unlift_gcode_input = QTextEdit()

        # Input groups
        self.start_point_group = QGroupBox(title="Start Point")
        self.max_point_group = QGroupBox(title="Max Point")
        self.normal_feedrate_group = QGroupBox(title="Normal Feedrate")
        self.travel_feedrate_group = QGroupBox(title="Travel Feedrate")
        self.curve_resolution_group = QGroupBox(title="Curve Resolution")
        self.start_gcode_group = QGroupBox(title="Start Gcode")
        self.end_gcode_group = QGroupBox(title="End Gcode")
        self.lift_gcode_group = QGroupBox(title="Lift Gcode")
        self.unlift_gcode_group = QGroupBox(title="Unlift Gcode")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self._load_options_file)
        self.save_to_file_button = QPushButton("Save to file")
        self.save_to_file_button.clicked.connect(self._save_options_file)

    def _create_layouts(self):
        """"""
        self.main_layout = QVBoxLayout()

        # Input layouts
        self.start_point_layout = QHBoxLayout()
        self.max_point_layout = QHBoxLayout()
        self.normal_feedrate_layout = QHBoxLayout()
        self.travel_feedrate_layout = QHBoxLayout()
        self.curve_resolution_layout = QHBoxLayout()
        self.start_gcode_layout = QHBoxLayout()
        self.end_gcode_layout = QHBoxLayout()
        self.lift_gcode_layout = QHBoxLayout()
        self.unlift_gcode_layout = QHBoxLayout()

        self.button_layout = QHBoxLayout()

        self.start_point_layout.addWidget(self.start_x_input)
        self.start_point_layout.addWidget(self.start_y_input)
        self.max_point_layout.addWidget(self.max_x_input)
        self.max_point_layout.addWidget(self.max_y_input)
        self.normal_feedrate_layout.addWidget(self.normal_feedrate_input)
        self.travel_feedrate_layout.addWidget(self.travel_feedrate_input)
        self.curve_resolution_layout.addWidget(self.curve_resolution_input)
        self.start_gcode_layout.addWidget(self.start_gcode_input)
        self.end_gcode_layout.addWidget(self.end_gcode_input)
        self.lift_gcode_layout.addWidget(self.lift_gcode_input)
        self.unlift_gcode_layout.addWidget(self.unlift_gcode_input)

        self.start_point_group.setLayout(self.start_point_layout)
        self.max_point_group.setLayout(self.max_point_layout)
        self.normal_feedrate_group.setLayout(self.normal_feedrate_layout)
        self.travel_feedrate_group.setLayout(self.travel_feedrate_layout)
        self.curve_resolution_group.setLayout(self.curve_resolution_layout)
        self.start_gcode_group.setLayout(self.start_gcode_layout)
        self.end_gcode_group.setLayout(self.end_gcode_layout)
        self.lift_gcode_group.setLayout(self.lift_gcode_layout)
        self.unlift_gcode_group.setLayout(self.unlift_gcode_layout)

        self.button_layout.addWidget(self.load_button)
        self.button_layout.addWidget(self.save_to_file_button)

        groups = (
            self.start_point_group,
            self.max_point_group,
            self.normal_feedrate_group,
            self.travel_feedrate_group,
            self.curve_resolution_group,
            self.start_gcode_group,
            self.end_gcode_group,
            self.lift_gcode_group,
            self.unlift_gcode_group,
        )

        content = QWidget()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)

        for group in groups:
            content_layout.addWidget(group)

        self.scroll_area.setWidget(content)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.status_bar)

        self.setLayout(self.main_layout)

    def _read_float(self, text_box: QTextEdit, error_message: str) -> float | None:
        str_value = text_box.toPlainText()
        try:
            float_value = float(str_value)
        except ValueError:
            return None
        return float_value

    def _read_int(self, text_box: QTextEdit, error_message: str) -> int | None:
        str_value = text_box.toPlainText()
        try:
            int_value = int(str_value)
        except ValueError:
            return None
        return int_value

    def _update_option_text_fields(self):
        if not self.options:
            return
        self.start_x_input.setPlainText(str(self.options.start_point.real))
        self.start_y_input.setPlainText(str(self.options.start_point.imag))

        if isinstance(self.options.max_point, complex):
            self.max_x_input.setPlainText(str(self.options.max_point.real))
            self.max_y_input.setPlainText(str(self.options.max_point.imag))

        self.normal_feedrate_input.setPlainText(str(self.options.normal_feedrate))
        self.travel_feedrate_input.setPlainText(str(self.options.travel_feedrate))

        self.curve_resolution_input.setPlainText(str(self.options.curve_resolution))

        self.start_gcode_input.setPlainText("\n".join(self.options.start_gcode))
        self.end_gcode_input.setPlainText("\n".join(self.options.end_gcode))
        self.lift_gcode_input.setPlainText("\n".join(self.options.lift_gcode))
        self.unlift_gcode_input.setPlainText("\n".join(self.options.unlift_gcode))

    @Slot()
    def _load_options_file(self):

        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter("TOML (*.toml)")
        dialog.setViewMode(QFileDialog.ViewMode.List)
        dialog.exec()
        selected_files = dialog.selectedFiles()

        if not selected_files:
            return

        self.load_options(pathlib.Path(selected_files[0]))

    @Slot()
    def _save_options_file(self):
        if not self.options:
            return

        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            filter="TOML (*.toml)",
            selectedFilter="TOML (*.toml)",
        )
        if not fileName:
            return

        error = None
        file = QSaveFile(fileName)
        if file.open(QFile.OpenModeFlag.WriteOnly | QFile.OpenModeFlag.Text):
            outf = QTextStream(file)
            _ = outf << tomli_w.dumps(self.options.get_dict())

            if not file.commit():
                reason = file.errorString()
                error = f"Cannot write file {fileName}:\n{reason}."
        else:
            reason = file.errorString()
            error = f"Cannot open file {fileName}:\n{reason}."

        if error:
            QMessageBox.warning(self, "Application", error)
            return False

        self.status_bar.showMessage(f"Config written to {fileName}")

    def load_options(self, file: pathlib.Path):
        """"""
        with file.open("rb") as f:
            data = tomllib.load(f)

        point_data: dict[str, int] | None = data.get("point")
        if point_data:
            start_point = complex(
                point_data.get("start_x") or 0, point_data.get("start_y") or 0
            )
            max_x = point_data.get("max_x")
            max_y = point_data.get("max_y")
            if max_x and max_y:
                max_point = complex(max_x, max_y)
            else:
                max_point = None
        else:
            start_point = DEFAULT_START_POINT
            max_point = DEFAULT_MAX_POINT

        machine_data: dict[str, int] | None = data.get("machine")
        if machine_data:
            normal_feedrate = (
                machine_data.get("normal_feedrate") or DEFAULT_NORMAL_FEEDRATE
            )
            travel_feedrate = (
                machine_data.get("travel_feedrate") or DEFAULT_TRAVEL_FEEDRATE
            )
            curve_resolution = (
                machine_data.get("curve_resolution") or DEFAULT_CURVE_RESOLUTION
            )
        else:
            normal_feedrate = DEFAULT_NORMAL_FEEDRATE
            travel_feedrate = DEFAULT_TRAVEL_FEEDRATE
            curve_resolution = DEFAULT_CURVE_RESOLUTION

        gcode_data: dict[str, list[str]] | None = data.get("gcode")
        if gcode_data:
            start_gcode = gcode_data.get("start") or DEFAULT_START_GCODE
            end_gcode = gcode_data.get("end") or DEFAULT_START_GCODE
            lift_gcode = gcode_data.get("lift") or DEFAULT_LIFT_GCODE
            unlift_gcode = gcode_data.get("unlift") or DEFAULT_UNLIFT_GCODE
        else:
            start_gcode = DEFAULT_START_GCODE
            end_gcode = DEFAULT_START_GCODE
            lift_gcode = DEFAULT_LIFT_GCODE
            unlift_gcode = DEFAULT_UNLIFT_GCODE

        if hasattr(self, "options") and isinstance(self.options, SlicingOptions):
            self.options.start_point = start_point
            self.options.max_point = max_point
            self.options.normal_feedrate = normal_feedrate
            self.options.travel_feedrate = travel_feedrate
            self.options.curve_resolution = curve_resolution
            self.options.start_gcode = start_gcode
            self.options.end_gcode = end_gcode
            self.options.lift_gcode = lift_gcode
            self.options.unlift_gcode = unlift_gcode
            self.options.max_point = max_point
        else:
            self.options = SlicingOptions(
                start_point=start_point,
                max_point=max_point,
                normal_feedrate=normal_feedrate,
                travel_feedrate=travel_feedrate,
                curve_resolution=curve_resolution,
                start_gcode=start_gcode,
                end_gcode=end_gcode,
                lift_gcode=lift_gcode,
                unlift_gcode=unlift_gcode,
            )

        self._update_option_text_fields()
        self.status_bar.showMessage(f"Loaded options {file}")

    def load_default(self):
        if not DEFAULT_TOML_PATH.is_file():
            self.status_bar.showMessage(
                f"Could not find options file at {DEFAULT_TOML_PATH}"
            )
            self.options = SlicingOptions(
                start_point=DEFAULT_START_POINT,
                max_point=DEFAULT_MAX_POINT,
                normal_feedrate=DEFAULT_NORMAL_FEEDRATE,
                travel_feedrate=DEFAULT_TRAVEL_FEEDRATE,
                curve_resolution=DEFAULT_CURVE_RESOLUTION,
                start_gcode=DEFAULT_START_GCODE,
                end_gcode=DEFAULT_END_GCODE,
                lift_gcode=DEFAULT_LIFT_GCODE,
                unlift_gcode=DEFAULT_UNLIFT_GCODE,
            )
            self._update_option_text_fields()
            return
        self.load_options(DEFAULT_TOML_PATH)

    def update_options(self):
        """"""
        start_point = complex(
            self._read_float(self.start_x_input, "Starting X point is not a float")
            or 0.0,
            self._read_float(self.start_y_input, "Starting Y point is not a float")
            or 0.0,
        )
        max_point = complex(
            self._read_float(self.max_x_input, "Starting X point is not a float")
            or 0.0,
            self._read_float(self.max_y_input, "Starting Y point is not a float")
            or 0.0,
        )
        normal_feedrate = (
            self._read_int(
                self.normal_feedrate_input, "Normal feedrate is not a integer"
            )
            or DEFAULT_NORMAL_FEEDRATE
        )
        travel_feedrate = (
            self._read_int(
                self.travel_feedrate_input, "Travel feedrate is not a integer"
            )
            or DEFAULT_TRAVEL_FEEDRATE
        )
        curve_resolution = (
            self._read_int(
                self.curve_resolution_input, "Curve resolution is not a integer"
            )
            or DEFAULT_CURVE_RESOLUTION
        )
        start_gcode = (
            self.start_gcode_input.toPlainText().splitlines() or DEFAULT_START_GCODE
        )
        end_gcode = self.end_gcode_input.toPlainText().splitlines() or DEFAULT_END_GCODE
        lift_gcode = (
            self.lift_gcode_input.toPlainText().splitlines() or DEFAULT_LIFT_GCODE
        )
        unlift_gcode = (
            self.unlift_gcode_input.toPlainText().splitlines() or DEFAULT_UNLIFT_GCODE
        )

        if hasattr(self, "options") and isinstance(self.options, SlicingOptions):
            self.options.start_point = start_point
            self.options.max_point = max_point
            self.options.normal_feedrate = normal_feedrate
            self.options.travel_feedrate = travel_feedrate
            self.options.curve_resolution = curve_resolution
            self.options.start_gcode = start_gcode
            self.options.end_gcode = end_gcode
            self.options.lift_gcode = lift_gcode
            self.options.unlift_gcode = unlift_gcode
            self.options.max_point = max_point
        else:
            self.options = SlicingOptions(
                start_point=start_point,
                max_point=max_point,
                normal_feedrate=normal_feedrate,
                travel_feedrate=travel_feedrate,
                curve_resolution=curve_resolution,
                start_gcode=start_gcode,
                end_gcode=end_gcode,
                lift_gcode=lift_gcode,
                unlift_gcode=unlift_gcode,
            )
