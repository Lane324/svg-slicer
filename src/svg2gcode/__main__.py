"""GUI app for svg2gcode"""

import pathlib
import sys

from PySide6.QtCore import QFile, QSaveFile, QTextStream, Slot

# pylint: disable=no-name-in-module
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from svg2gcode import gcode_generator, gcode_viewer
from svg2gcode.gcode_generator import GcodeGenerator
from svg2gcode.slicing_options import SlicingOptionsWiget


class MainWindow(QMainWindow):
    """Main window for GUI app"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        """Creates MainWindow"""
        super().__init__()

        self.setWindowTitle("Gcode Generator")
        self.create_menu()
        self.setUnifiedTitleAndToolBarOnMac(True)

        self.selected_svg: pathlib.Path | None = None

        self.slicing_options_widget = SlicingOptionsWiget()
        self.gcode_generator: GcodeGenerator = GcodeGenerator(
            self.slicing_options_widget.options
        )
        self.points: list[gcode_generator.GcodePoint] | None = None

        # Widgets
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        self.select_file_button = QPushButton("Open SVG")
        self.selected_file_label = QLabel()
        self.selected_file_label.setText("Please open SVG...")
        self.generate_gcode_button = QPushButton("Generate")
        self.save_file_button = QPushButton("Save")
        self.svg_scene = QGraphicsScene()
        self.svg_viewer = QGraphicsView(self.svg_scene)

        self.gcode_viewer = gcode_viewer.GcodeViewer()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.svg_viewer, "SVG")
        self.tabs.addTab(self.gcode_viewer, "Gcode")
        self.tabs.addTab(self.slicing_options_widget, "Options")

        # Connections
        self.select_file_button.clicked.connect(self.select_svg)
        self.generate_gcode_button.clicked.connect(self.generate_gcode)
        self.save_file_button.clicked.connect(self.save_file)

        # Layouts
        main_layout = QVBoxLayout()
        file_selection_layout = QHBoxLayout()
        file_generation_layout = QHBoxLayout()

        # Add widgets to layouts
        file_selection_layout.addWidget(self.select_file_button)
        file_selection_layout.addWidget(self.selected_file_label)
        file_generation_layout.addWidget(self.generate_gcode_button)
        file_generation_layout.addWidget(self.save_file_button)
        main_layout.addLayout(file_selection_layout)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(file_generation_layout)
        self.setLayout(main_layout)

        main_widget.setLayout(main_layout)

    @Slot()
    def select_svg(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter("SVG (*.svg)")
        dialog.setViewMode(QFileDialog.ViewMode.List)
        dialog.exec()
        selected_files = dialog.selectedFiles()

        if not selected_files:
            return

        self.selected_svg = pathlib.Path(selected_files[0])
        self.selected_file_label.setText(f"Selected file: {str(self.selected_svg)}")
        svg_item = QGraphicsSvgItem(str(self.selected_svg))
        self.svg_scene.clear()
        self.svg_scene.addItem(svg_item)

    @Slot()
    def generate_gcode(self):
        if not self.selected_svg:
            self.select_svg()
        if not self.selected_svg:
            return

        self.statusBar().showMessage("Gcode generation started...")
        self.slicing_options_widget.update_options()
        self.gcode_generator.update_options(self.slicing_options_widget.options)
        self.gcode_generator.generate_gcode(self.selected_svg)
        self.statusBar().showMessage("Gcode generated!", 2000)
        self.gcode_viewer.load_gcode(self.gcode_generator.gcode)

    @Slot()
    def save_file(self):
        if not self.gcode_generator.gcode:
            return

        fileName, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            filter="Gcode Files (*.gcode)",
            selectedFilter="Gcode Files (*.gcode)",
        )
        if not fileName:
            return

        error = None
        file = QSaveFile(fileName)
        if file.open(QFile.OpenModeFlag.WriteOnly | QFile.OpenModeFlag.Text):
            outf = QTextStream(file)
            string = "\n".join(self.gcode_generator.gcode)
            _ = outf << string

            if not file.commit():
                reason = file.errorString()
                error = f"Cannot write file {fileName}:\n{reason}."
        else:
            reason = file.errorString()
            error = f"Cannot open file {fileName}:\n{reason}."

        if error:
            QMessageBox.warning(self, "Application", error)
            return False

        self.statusBar().showMessage(f"Gcode written to {fileName}")

    def create_menu(self):
        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction("Open SVG", self.select_svg)
        self._file_menu.addAction("Generate Gcode", self.generate_gcode)
        self._file_menu.addAction("Save Gcode", self.save_file)
        self._file_menu.addSeparator()
        self._file_menu.addAction("Exit", self.close)


def main():
    """Main entry point for svg2gcode"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.showMaximized()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
