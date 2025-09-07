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
    label: str
    maximum: int | None = None
    minimum: int | None = None
    prefix: str | None = None
    suffix: str | None = None


class LabeledSpinBox(QWidget):
    def __init__(
        self,
        label_text: str,
        maximum: int | None = None,
        minimum: int | None = None,
        prefix: str | None = None,
        suffix: str | None = None,
    ):
        super().__init__()

        self.spinbox: QSpinBox | QDoubleSpinBox
        self.value: int = 0

        layout = QHBoxLayout()
        label = QLabel()
        label.setText(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.spinbox = QSpinBox()
        if maximum:
            self.spinbox.setMaximum(maximum)
        if minimum:
            self.spinbox.setMinimum(minimum)
        if prefix:
            self.spinbox.setPrefix(prefix)
        if suffix:
            self.spinbox.setSuffix(suffix)

        layout.addWidget(label)
        layout.addWidget(self.spinbox)
        self.setLayout(layout)


class LabeledDoubleSpinBox(QWidget):
    def __init__(
        self,
        label_text: str,
        maximum: int | None = None,
        minimum: int | None = None,
        prefix: str | None = None,
        suffix: str | None = None,
    ):
        super().__init__()

        self.value: float = 0.0

        layout = QHBoxLayout()
        label = QLabel()
        label.setText(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.spinbox = QDoubleSpinBox()
        if maximum:
            self.spinbox.setMaximum(maximum)
        if minimum:
            self.spinbox.setMinimum(minimum)
        if prefix:
            self.spinbox.setPrefix(prefix)
        if suffix:
            self.spinbox.setSuffix(suffix)

        layout.addWidget(label)
        layout.addWidget(self.spinbox)
        self.setLayout(layout)


class MultiLabeledSpinBox(QWidget):
    def __init__(
        self,
        title: str,
        configs: tuple[LabeledSpinBoxConfig, ...],
    ):
        super().__init__()
        self.group_box = QGroupBox(title=title)
        spinbox_layout = QVBoxLayout()

        self.spinboxes: list[LabeledSpinBox] = []
        for config in configs:
            new_widget = LabeledSpinBox(
                label_text=config.label,
                maximum=config.maximum,
                minimum=config.minimum,
                prefix=config.prefix,
                suffix=config.suffix,
            )
            self.spinboxes.append(new_widget)
            spinbox_layout.addWidget(new_widget)

        self.group_box.setLayout(spinbox_layout)
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.group_box)

        self.setLayout(mainlayout)


class MultiLabeledDoubleSpinBox(QWidget):
    def __init__(
        self,
        title: str,
        configs: tuple[LabeledSpinBoxConfig, ...],
    ):
        super().__init__()
        self.group_box = QGroupBox(title=title)
        spinbox_layout = QVBoxLayout()

        self.spinboxes: list[LabeledDoubleSpinBox] = []
        for config in configs:
            new_widget = LabeledDoubleSpinBox(
                label_text=config.label,
                maximum=config.maximum,
                minimum=config.minimum,
                prefix=config.prefix,
                suffix=config.suffix,
            )
            self.spinboxes.append(new_widget)
            spinbox_layout.addWidget(new_widget)

        self.group_box.setLayout(spinbox_layout)
        mainlayout = QVBoxLayout()
        mainlayout.addWidget(self.group_box)

        self.setLayout(mainlayout)
