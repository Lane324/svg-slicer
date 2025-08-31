"""GUI app for svg-slicer"""

import pathlib
import sys

# pylint: disable=no-name-in-module
from PySide6.QtCore import Slot
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from svg_slicer import gcode_generator, gcode_viewer, helpers
from svg_slicer.gcode_generator import GcodeGenerator
from svg_slicer.slicing_options import SlicingOptionsWiget


class MainWindow(QMainWindow):
    """Main window for GUI app"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        """Creates MainWindow"""
        super().__init__()

        self.setWindowTitle("Gcode Generator")

        self._create_menu()
        self._create_widgets()
        self._create_layouts()

        self.selected_svg: pathlib.Path | None = None

        self.gcode_generator: GcodeGenerator = GcodeGenerator(
            self.slicing_options_widget.options
        )
        self.points: list[gcode_generator.GcodePoint] | None = None

    def _create_menu(self):
        """Creates menu"""
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction("Open SVG", self.select_svg)
        self._file_menu.addAction("Generate Gcode", self.generate_gcode)
        self._file_menu.addAction("Save Gcode", self.save_file)
        self._file_menu.addSeparator()
        self._file_menu.addAction("Exit", self.close)

    def _create_widgets(self):
        """Creates all subwidgets"""
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.select_file_button = QPushButton("Open SVG")
        self.selected_file_label = QLabel()
        self.selected_file_label.setText("Please open SVG...")
        self.generate_gcode_button = QPushButton("Generate")
        self.save_file_button = QPushButton("Save")
        self.svg_scene = QGraphicsScene()
        self.svg_viewer = QGraphicsView(self.svg_scene)

        self.gcode_viewer = gcode_viewer.GcodeViewerWidget()

        self.slicing_options_widget = SlicingOptionsWiget()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.svg_viewer, "SVG")
        self.tabs.addTab(self.gcode_viewer, "Gcode")
        self.tabs.addTab(self.slicing_options_widget, "Options")

        self._connect_widgets()

    def _connect_widgets(self):
        """Connects widgets to their slots"""
        self.select_file_button.clicked.connect(self.select_svg)
        self.generate_gcode_button.clicked.connect(self.generate_gcode)
        self.save_file_button.clicked.connect(self.save_file)

    def _create_layouts(self):
        """Creates and congiures all layouts in widget"""
        main_layout = QVBoxLayout()
        file_selection_layout = QHBoxLayout()
        file_generation_layout = QHBoxLayout()
        file_selection_layout.addWidget(self.select_file_button)
        file_selection_layout.addWidget(self.selected_file_label)
        file_generation_layout.addWidget(self.generate_gcode_button)
        file_generation_layout.addWidget(self.save_file_button)
        main_layout.addLayout(file_selection_layout)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(file_generation_layout)
        self.setLayout(main_layout)

        self.main_widget.setLayout(main_layout)

    @Slot()
    def select_svg(self):
        """File dialog to select SVG file to slice"""
        selected_files = helpers.select_files()
        if not selected_files:
            return

        self.selected_svg = pathlib.Path(selected_files[0])
        self.selected_file_label.setText(f"Selected file: {str(self.selected_svg)}")
        svg_item = QGraphicsSvgItem(str(self.selected_svg))
        self.svg_scene.clear()
        self.svg_scene.addItem(svg_item)

    @Slot()
    def generate_gcode(self):
        """Slices selected SVG or prompts to select SVG"""
        if not self.selected_svg:
            self.select_svg()
        if not self.selected_svg:
            return

        self.statusBar().showMessage("Gcode generation started...")
        self.slicing_options_widget.update_options()
        self.gcode_generator.set_options(self.slicing_options_widget.options)
        self.gcode_generator.generate_gcode(self.selected_svg)
        self.statusBar().showMessage("Gcode generated!", 2000)
        self.gcode_viewer.load_gcode(self.gcode_generator.gcode)

    @Slot()
    def save_file(self):
        """File dialog to save gcode file"""
        if not self.gcode_generator.gcode:
            return

        file_name = helpers.save_file(
            self, "\n".join(self.gcode_generator.gcode), "Gcode Files (*.gcode)"
        )

        self.statusBar().showMessage(f"Gcode written to {file_name}")


def main():
    """Main entry point for svg-slicer"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.showMaximized()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
