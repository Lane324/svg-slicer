"""Tests svg_slicer.helpers"""

# pylint: disable=invalid-name

import pathlib
from unittest import mock

import pytest

# pylint: disable=no-name-in-module
from PySide6.QtCore import QSaveFile, QTextStream
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from pytestqt.qtbot import QtBot

from svg_slicer import helpers


# region save_file
def test_save_file_saves_content(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
):
    """Tests that a file is saved with the correct contents and no warnings raised"""
    save_file = tmp_path / "saved_file.txt"
    file_contents = "qwerty"

    mock_getSaveFileName: mock.MagicMock = mock.create_autospec(
        QFileDialog.getSaveFileName, return_value=(str(save_file), None)
    )
    monkeypatch.setattr(helpers.QFileDialog, "getSaveFileName", mock_getSaveFileName)

    mock_QSaveFile: mock.MagicMock = mock.create_autospec(
        QSaveFile, return_value=QSaveFile(str(save_file))
    )
    monkeypatch.setattr(helpers, "QSaveFile", mock_QSaveFile)

    mock_warning: mock.MagicMock = mock.create_autospec(QMessageBox.warning)
    monkeypatch.setattr(helpers.QMessageBox, "warning", mock_warning)

    widget = QWidget()
    qtbot.addWidget(widget)

    helpers.save_file(widget, file_contents, "Text Files (*.txt)")

    mock_warning.assert_not_called()
    assert save_file.is_file()
    assert save_file.read_text() == file_contents


def test_save_file_select_no_files(monkeypatch: pytest.MonkeyPatch):
    """Tests that no file is saved when no file is selected and no warnings raised"""
    mock_getSaveFileName: mock.MagicMock = mock.create_autospec(
        QFileDialog.getSaveFileName, return_value=("", None)
    )
    monkeypatch.setattr(helpers.QFileDialog, "getSaveFileName", mock_getSaveFileName)

    mock_QSaveFile: mock.MagicMock = mock.create_autospec(QSaveFile)
    monkeypatch.setattr(helpers, "QSaveFile", mock_QSaveFile)

    mock_warning: mock.MagicMock = mock.create_autospec(QMessageBox.warning)
    monkeypatch.setattr(helpers.QMessageBox, "warning", mock_warning)

    assert not helpers.save_file(QWidget(), "qwerty", "Text Files (*.txt)")
    mock_QSaveFile.assert_not_called()
    mock_warning.assert_not_called()


def test_save_file_warns_on_open_error(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
):
    """Tests that warning is raised when file open fails"""
    save_file = tmp_path / "saved_file.txt"
    error_msg = "failed to open file"

    mock_getSaveFileName: mock.MagicMock = mock.create_autospec(
        QFileDialog.getSaveFileName, return_value=(str(save_file), None)
    )
    monkeypatch.setattr(helpers.QFileDialog, "getSaveFileName", mock_getSaveFileName)

    mock_QSaveFile: mock.MagicMock = mock.create_autospec(QSaveFile)
    mock_file_instance = mock_QSaveFile.return_value
    mock_file_instance.open.return_value = False
    mock_file_instance.errorString.return_value = error_msg
    monkeypatch.setattr(helpers, "QSaveFile", mock_QSaveFile)

    mock_warning: mock.MagicMock = mock.create_autospec(QMessageBox.warning)
    monkeypatch.setattr(helpers.QMessageBox, "warning", mock_warning)

    widget = QWidget()
    qtbot.addWidget(widget)

    assert not helpers.save_file(widget, "qwerty", "Text Files (*.txt)")
    mock_warning.assert_called_once_with(
        widget, "Application", f"Cannot open file {str(save_file)}:\n{error_msg}."
    )
    assert not save_file.exists()


def test_save_file_warns_on_commit_error(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot
):
    """Tests that warning is raised when file commit fails"""
    save_file = tmp_path / "saved_file.txt"
    error_msg = "failed to commit to file"

    mock_getSaveFileName: mock.MagicMock = mock.create_autospec(
        QFileDialog.getSaveFileName, return_value=(str(save_file), None)
    )
    monkeypatch.setattr(helpers.QFileDialog, "getSaveFileName", mock_getSaveFileName)

    mock_QSaveFile: mock.MagicMock = mock.create_autospec(QSaveFile)
    mock_file_instance = mock_QSaveFile.return_value
    mock_file_instance.open.return_value = True
    mock_file_instance.commit.return_value = False
    mock_file_instance.errorString.return_value = error_msg
    monkeypatch.setattr(helpers, "QSaveFile", mock_QSaveFile)

    mock_QTextStream: mock.MagicMock = mock.create_autospec(QTextStream)
    monkeypatch.setattr(helpers, "QTextStream", mock_QTextStream)

    mock_warning: mock.MagicMock = mock.create_autospec(QMessageBox.warning)
    monkeypatch.setattr(helpers.QMessageBox, "warning", mock_warning)

    widget = QWidget()
    qtbot.addWidget(widget)

    assert not helpers.save_file(widget, "qwerty", "Text Files (*.txt)")
    mock_warning.assert_called_once_with(
        widget, "Application", f"Cannot write file {str(save_file)}:\n{error_msg}."
    )
    assert not save_file.exists()


# endregion
# region select_files


def test_selecting_files_returns_files(monkeypatch: pytest.MonkeyPatch):
    """Tests that selecting files returns the files selected"""
    selected_files = ("file1.txt", "file2.txt")
    file_filter = "txt (*.txt)"

    mock_QFileDialog: mock.MagicMock = mock.create_autospec(QFileDialog)
    mock_file_dialog_instance = mock_QFileDialog.return_value
    mock_file_dialog_instance.exec.return_value = True
    mock_file_dialog_instance.selectedFiles.return_value = selected_files
    monkeypatch.setattr(helpers, "QFileDialog", mock_QFileDialog)

    assert helpers.select_files(file_filter) == selected_files

    mock_file_dialog_instance.setNameFilter.assert_called_once_with(file_filter)
    mock_file_dialog_instance.exec.assert_called_once()


# endregion
