"""Helper functions for svg_slicer"""

# pylint: disable=no-name-in-module
from PySide6.QtCore import QFile, QSaveFile, QTextStream
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget


def save_file(widget: QWidget, file_contents: str, file_filter: str) -> str | None:
    """
    File dialog to save file

    Args:
        widget: parent widget
        file_contents: content to write to file
        file_filter: filter to apply to fie dialog

    Returns:
        path to file saved to
    """
    file_name, _ = QFileDialog.getSaveFileName(
        widget,
        "Save File",
        filter=file_filter,
        selectedFilter=file_filter,
    )
    if not file_name:
        return None

    error = None
    file = QSaveFile(file_name)
    if file.open(QFile.OpenModeFlag.WriteOnly | QFile.OpenModeFlag.Text):
        outf = QTextStream(file)
        _ = outf << file_contents

        if not file.commit():
            reason = file.errorString()
            error = f"Cannot write file {file_name}:\n{reason}."
    else:
        reason = file.errorString()
        error = f"Cannot open file {file_name}:\n{reason}."

    if error:
        QMessageBox.warning(widget, "Application", error)
        return None

    return file_name


def select_files() -> list[str]:
    """
    File dialog to select files

    Returns:
        selected files
    """
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    dialog.setNameFilter("TOML (*.toml)")
    dialog.setViewMode(QFileDialog.ViewMode.List)
    dialog.exec()
    return dialog.selectedFiles()
