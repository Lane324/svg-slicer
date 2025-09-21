"""
Custom widgets
"""

from typing import NamedTuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class LabeledSpinBoxConfig(NamedTuple):
    """Config data for labeled spin boxes"""

    label: str
    maximum: int | None = None
    minimum: int | None = None
    prefix: str | None = None
    suffix: str | None = None


class LabeledSpinBox(QWidget):
    """Labeled Spinbox widget"""

    def __init__(self, config: LabeledSpinBoxConfig):
        """Creates LabeledSpinBox widget"""
        super().__init__()

        self.spinbox: QSpinBox | QDoubleSpinBox
        self.value: int = 0

        layout = QHBoxLayout()
        label = QLabel()
        label.setText(config.label)
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.spinbox = QSpinBox()
        if config.maximum:
            self.spinbox.setMaximum(config.maximum)
        if config.minimum:
            self.spinbox.setMinimum(config.minimum)
        if config.prefix:
            self.spinbox.setPrefix(config.prefix)
        if config.suffix:
            self.spinbox.setSuffix(config.suffix)

        layout.addWidget(label)
        layout.addWidget(self.spinbox)
        self.setLayout(layout)


class LabeledDoubleSpinBox(QWidget):
    """Labeled Double Spinbox widget"""

    def __init__(self, config):
        """Creates LabeledDoubleSpinBox widget"""
        super().__init__()

        self.value: float = 0.0

        layout = QHBoxLayout()
        label = QLabel()
        label.setText(config.label)
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.spinbox = QDoubleSpinBox()
        if config.maximum:
            self.spinbox.setMaximum(config.maximum)
        if config.minimum:
            self.spinbox.setMinimum(config.minimum)
        if config.prefix:
            self.spinbox.setPrefix(config.prefix)
        if config.suffix:
            self.spinbox.setSuffix(config.suffix)

        layout.addWidget(label)
        layout.addWidget(self.spinbox)
        self.setLayout(layout)


class MultiLabeledSpinBox(QWidget):
    """Multi Labeled Spinbox widget"""

    def __init__(
        self,
        title: str,
        configs: tuple[LabeledSpinBoxConfig, ...],
    ):
        """Creates MultiLabeledSpinBox widget"""
        super().__init__()
        self.group_box = QGroupBox(title=title)
        spinbox_layout = QVBoxLayout()

        self.spinboxes: list[LabeledSpinBox] = []
        for config in configs:
            new_widget = LabeledSpinBox(config)
            self.spinboxes.append(new_widget)
            spinbox_layout.addWidget(new_widget)

        self.group_box.setLayout(spinbox_layout)
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.group_box)

        self.setLayout(mainlayout)


class MultiLabeledDoubleSpinBox(QWidget):
    """Labeled Spinbox widget"""

    def __init__(
        self,
        title: str,
        configs: tuple[LabeledSpinBoxConfig, ...],
    ):
        """Creates MultiLabeledDoubleSpinBox widget"""
        super().__init__()
        self.group_box = QGroupBox(title=title)
        spinbox_layout = QVBoxLayout()

        self.spinboxes: list[LabeledDoubleSpinBox] = []
        for config in configs:
            new_widget = LabeledDoubleSpinBox(config)
            self.spinboxes.append(new_widget)
            spinbox_layout.addWidget(new_widget)

        self.group_box.setLayout(spinbox_layout)
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.group_box)

        self.setLayout(mainlayout)
