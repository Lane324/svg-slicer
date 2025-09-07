"""
Holds slicing options
"""

import pathlib
import tomllib
from dataclasses import dataclass
from typing import Iterable

import tomli_w
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from svg_slicer import helpers
from svg_slicer.widgets.labeled_spin_box import (
    LabeledDoubleSpinBox,
    LabeledSpinBox,
    LabeledSpinBoxConfig,
    MultiLabeledSpinBox,
)

DEFAULT_TOML_PATH = (
    pathlib.Path().home() / "AppData" / "Roaming" / "svg-slicer" / "svg-slicer.toml"
)

DEFAULT_START_POINT: complex = complex(1, 1)
DEFAULT_NORMAL_FEEDRATE: int = 500
DEFAULT_TRAVEL_FEEDRATE: int = 4000
DEFAULT_CURVE_RESOLUTION: int = 20
DEFAULT_BLADE_OFFSET: float = 0.0
DEFAULT_START_GCODE: tuple[str, ...] = (
    "; start",
    "M107 ; turn fan off",
    "G21 ; use millimeter",
    "G90 ; absolute coordinates",
    "M82 ; absolute E coordinates",
    "G92 E0 ; set E to 0",
    "G28 ; home xyz axes",
    "G1 F500 ; set feedrate",
    "",
)
DEFAULT_END_GCODE: tuple[str, ...] = ("; end",)
DEFAULT_LIFT_GCODE: tuple[str, ...] = ("G1 Z10",)
DEFAULT_UNLIFT_GCODE: tuple[str, ...] = ("G1 Z0",)


# pylint: disable=too-many-instance-attributes
@dataclass
class SlicingOptions:
    """Holds slicing options"""

    start_point: complex = DEFAULT_START_POINT
    normal_feedrate: int = DEFAULT_NORMAL_FEEDRATE
    travel_feedrate: int = DEFAULT_TRAVEL_FEEDRATE
    curve_resolution: int = DEFAULT_CURVE_RESOLUTION
    blade_offset: float = DEFAULT_BLADE_OFFSET
    start_gcode: Iterable[str] = DEFAULT_START_GCODE
    end_gcode: Iterable[str] = DEFAULT_END_GCODE
    lift_gcode: Iterable[str] = DEFAULT_LIFT_GCODE
    unlift_gcode: Iterable[str] = DEFAULT_UNLIFT_GCODE

    def get_dict(self) -> dict:
        """Turns instance into a TOML serializable dic"""
        return {
            "machine": {
                "normal_feedrate": self.normal_feedrate,
                "travel_feedrate": self.travel_feedrate,
                "curve_resolution": self.curve_resolution,
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
            },
        }


class SlicingOptionsWiget(QWidget):
    """Widget to view and set slicer options"""

    def __init__(
        self,
        options: SlicingOptions | None = None,
        options_file: pathlib.Path | None = None,
    ):
        """Creates SlicingOptionsWiget"""
        super().__init__()

        self._create_widgets()
        self._connect_widgets()
        self._create_layouts()

        self.options: SlicingOptions
        if options:
            self.options = options
        elif options_file:
            self.options: SlicingOptions = SlicingOptions()
            self.load_options(options_file)
        else:
            self.options: SlicingOptions = SlicingOptions()
            self._load_default()

    def _create_widgets(self):
        """Creates all subwidgets"""
        self.status_bar = QStatusBar()

        # Input boxes
        self.start_point_selector = MultiLabeledSpinBox(
            title="Start Point",
            configs=(
                LabeledSpinBoxConfig(label="X", suffix=" mm"),
                LabeledSpinBoxConfig(label="Y", suffix=" mm"),
            ),
        )
        self.feedrate_selector = MultiLabeledSpinBox(
            title="Feedrates",
            configs=(
                LabeledSpinBoxConfig(label="Normal", suffix=" mm/min", maximum=10000),
                LabeledSpinBoxConfig(label="Travel", suffix=" mm/min", maximum=10000),
            ),
        )

        self.curve_resolution_spinbox = LabeledSpinBox(label_text="Curve Resolution")
        self.blade_offset_spinbox = LabeledDoubleSpinBox(label_text="Blade Offset")

        self.start_gcode_input = QTextEdit()
        self.end_gcode_input = QTextEdit()
        self.lift_gcode_input = QTextEdit()
        self.unlift_gcode_input = QTextEdit()

        # Input groups
        self.curve_resolution_group = QGroupBox(title="Curve Resolution")
        self.start_gcode_group = QGroupBox(title="Start Gcode")
        self.end_gcode_group = QGroupBox(title="End Gcode")
        self.lift_gcode_group = QGroupBox(title="Lift Gcode")
        self.unlift_gcode_group = QGroupBox(title="Unlift Gcode")

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.save_to_file_button = QPushButton("Save to file")
        self.load_button = QPushButton("Load")

    def _connect_widgets(self):
        """Connects widgets to their slots"""
        self.load_button.clicked.connect(self._load_options_file)
        self.save_to_file_button.clicked.connect(self._save_options_file)
        self.start_point_selector.spinboxes[0].spinbox.valueChanged.connect(
            self._start_x_changed
        )
        self.start_point_selector.spinboxes[1].spinbox.valueChanged.connect(
            self._start_y_changed
        )
        self.feedrate_selector.spinboxes[0].spinbox.valueChanged.connect(
            self._normal_feedrate_changed
        )
        self.feedrate_selector.spinboxes[1].spinbox.valueChanged.connect(
            self._travel_feedrate_changed
        )
        self.curve_resolution_spinbox.spinbox.valueChanged.connect(
            self._curve_resolution_changed
        )
        self.blade_offset_spinbox.spinbox.valueChanged.connect(
            self._blade_offset_changed
        )
        self.start_gcode_input.textChanged.connect(self._start_gcode_changed)
        self.end_gcode_input.textChanged.connect(self._end_gcode_changed)
        self.lift_gcode_input.textChanged.connect(self._lift_gcode_changed)
        self.unlift_gcode_input.textChanged.connect(self._unlift_gcode_changed)

    def _create_layouts(self):
        """Creates and congiures all layouts in widget"""
        self.main_layout = QVBoxLayout()

        # Input layouts
        self.point_feedrate_layout = QHBoxLayout()
        self.curve_resolution_layout = QVBoxLayout()
        self.start_gcode_layout = QHBoxLayout()
        self.end_gcode_layout = QHBoxLayout()
        self.lift_gcode_layout = QHBoxLayout()
        self.unlift_gcode_layout = QHBoxLayout()
        self.button_layout = QHBoxLayout()

        self.curve_resolution_layout.addWidget(self.curve_resolution_spinbox)
        self.curve_resolution_layout.addWidget(self.blade_offset_spinbox)
        self.curve_resolution_group.setLayout(self.curve_resolution_layout)
        self.point_feedrate_layout.addWidget(self.curve_resolution_group)

        self.point_feedrate_layout.addWidget(self.start_point_selector)
        self.point_feedrate_layout.addWidget(self.feedrate_selector)
        self.curve_resolution_group
        self.point_feedrate_layout.addWidget(self.curve_resolution_group)
        self.start_gcode_layout.addWidget(self.start_gcode_input)
        self.end_gcode_layout.addWidget(self.end_gcode_input)
        self.lift_gcode_layout.addWidget(self.lift_gcode_input)
        self.unlift_gcode_layout.addWidget(self.unlift_gcode_input)

        self.curve_resolution_group.setLayout(self.curve_resolution_layout)
        self.start_gcode_group.setLayout(self.start_gcode_layout)
        self.end_gcode_group.setLayout(self.end_gcode_layout)
        self.lift_gcode_group.setLayout(self.lift_gcode_layout)
        self.unlift_gcode_group.setLayout(self.unlift_gcode_layout)

        self.button_layout.addWidget(self.load_button)
        self.button_layout.addWidget(self.save_to_file_button)

        groups = (
            self.curve_resolution_group,
            self.start_gcode_group,
            self.end_gcode_group,
            self.lift_gcode_group,
            self.unlift_gcode_group,
        )

        content = QWidget()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)

        content_layout.addLayout(self.point_feedrate_layout)
        for group in groups:
            content_layout.addWidget(group)

        self.scroll_area.setWidget(content)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addWidget(self.status_bar)

        self.setLayout(self.main_layout)

    def _update_option_text_fields(self):
        """Update text fields with set options"""
        self.start_point_selector.spinboxes[0].spinbox.setValue(
            int(self.options.start_point.real)
        )
        self.start_point_selector.spinboxes[1].spinbox.setValue(
            int(self.options.start_point.imag)
        )

        self.feedrate_selector.spinboxes[0].spinbox.setValue(
            self.options.normal_feedrate
        )
        self.feedrate_selector.spinboxes[1].spinbox.setValue(
            self.options.travel_feedrate
        )

        self.curve_resolution_spinbox.spinbox.setValue(self.options.curve_resolution)
        self.blade_offset_spinbox.spinbox.setValue(self.options.blade_offset)

        self.start_gcode_input.setPlainText("\n".join(self.options.start_gcode))
        self.end_gcode_input.setPlainText("\n".join(self.options.end_gcode))
        self.lift_gcode_input.setPlainText("\n".join(self.options.lift_gcode))
        self.unlift_gcode_input.setPlainText("\n".join(self.options.unlift_gcode))

    @Slot()
    def _load_options_file(self):
        """File dialog to load options from file"""
        selected_files = helpers.select_files("TOML (*.toml)")
        if not selected_files:
            return

        self.load_options(pathlib.Path(selected_files[0]))

    @Slot()
    def _save_options_file(self):
        """File dialog to save currently set options to file"""
        file_name = helpers.save_file(
            self, tomli_w.dumps(self.options.get_dict()), "TOML (*.toml)"
        )

        self.status_bar.showMessage(f"Config written to {file_name}")

    @Slot()
    def _start_x_changed(self, new_value: int):
        self.options.start_point = complex(new_value, self.options.start_point.imag)

    @Slot()
    def _start_y_changed(self, new_value: int):
        self.options.start_point = complex(self.options.start_point.imag, new_value)

    @Slot()
    def _normal_feedrate_changed(self, new_value: int):
        self.options.normal_feedrate = new_value

    @Slot()
    def _travel_feedrate_changed(self, new_value: int):
        self.options.travel_feedrate = new_value

    @Slot()
    def _curve_resolution_changed(self, new_value: int):
        self.options.curve_resolution = new_value

    @Slot()
    def _blade_offset_changed(self, new_value: float):
        self.options.blade_offset = new_value

    @Slot()
    def _start_gcode_changed(self):
        self.options.start_gcode = self.start_gcode_input.toPlainText().splitlines()

    @Slot()
    def _end_gcode_changed(self):
        self.options.end_gcode = self.end_gcode_input.toPlainText().splitlines()

    @Slot()
    def _lift_gcode_changed(self):
        self.options.lift_gcode = self.lift_gcode_input.toPlainText().splitlines()

    @Slot()
    def _unlift_gcode_changed(self):
        self.options.unlift_gcode = self.unlift_gcode_input.toPlainText().splitlines()

    # pylint: disable=too-many-locals
    def load_options(self, file: pathlib.Path):
        """
        Load slicer options from a file

        Args:
            file: path to TOML file
        """
        with file.open("rb") as f:
            data = tomllib.load(f)

        if point_data := data.get("point"):
            self.options.start_point = complex(
                point_data.get("start_x") or DEFAULT_START_POINT.real,
                point_data.get("start_y") or DEFAULT_START_POINT.imag,
            )

        if machine_data := data.get("machine"):
            self.options.normal_feedrate = (
                machine_data.get("normal_feedrate") or DEFAULT_NORMAL_FEEDRATE
            )
            self.options.travel_feedrate = (
                machine_data.get("travel_feedrate") or DEFAULT_TRAVEL_FEEDRATE
            )
            self.options.curve_resolution = (
                machine_data.get("curve_resolution") or DEFAULT_CURVE_RESOLUTION
            )
            self.options.blade_offset = (
                machine_data.get("blade_offset") or DEFAULT_BLADE_OFFSET
            )

        if gcode_data := data.get("gcode"):
            self.options.start_gcode = gcode_data.get("start") or DEFAULT_START_GCODE
            self.options.end_gcode = gcode_data.get("end") or DEFAULT_END_GCODE
            self.options.lift_gcode = gcode_data.get("lift") or DEFAULT_LIFT_GCODE
            self.options.unlift_gcode = gcode_data.get("unlift") or DEFAULT_UNLIFT_GCODE

        self._update_option_text_fields()
        self.status_bar.showMessage(f"Loaded options from: {file}")

    def _load_default(self):
        """Loads slicer options from default config file"""
        if not DEFAULT_TOML_PATH.is_file():
            self.status_bar.showMessage(
                f"Could not find options file at {DEFAULT_TOML_PATH}"
            )
            return
        self.load_options(DEFAULT_TOML_PATH)
