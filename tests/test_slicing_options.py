"""
Tests svg_slicer.slicing_options
"""

import pathlib
from unittest import mock

import pytest
import tomli_w
from PySide6.QtWidgets import QTextEdit
from pytestqt.qtbot import QtBot

from svg_slicer import helpers, slicing_options

# pylint: disable=redefined-outer-name, protected-access, duplicate-code

# region Mocks


@pytest.fixture(autouse=True)
def mock_toml_file(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    """Creates mock options toml file with mock data"""
    toml_file = tmp_path / "options.toml"

    data = {
        "machine": {
            "normal_feedrate": 100,
            "travel_feedrate": 1000,
            "curve_resolution": 10,
        },
        "gcode": {
            "start": ["start"],
            "end": ["end"],
            "lift": ["lift"],
            "unlift": ["unlift"],
        },
        "point": {
            "start_x": 1.0,
            "start_y": 1.0,
            "max_x": 100.0,
            "max_y": 100.0,
        },
    }

    with toml_file.open("wb") as f:
        tomli_w.dump(data, f)

    monkeypatch.setattr(slicing_options, "DEFAULT_TOML_PATH", toml_file)


# endregion

# region SlicingOptions.get_dict


def test_slicing_get_dict():
    """Tests that turning the slicing options into a dict returns correct dict"""

    start_point = complex(1, 2)
    max_point = complex(10, 20)
    normal_feedrate = 500
    travel_feedrate = 4000
    curve_resolution = 20
    start_gcode = ["start_gcode"]
    end_gcode = ["end_gcode"]
    lift_gcode = ["lift_gcode"]
    unlift_gcode = ["unlift_gcode"]

    options = slicing_options.SlicingOptions(
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

    assert options.get_dict() == {
        "machine": {
            "normal_feedrate": normal_feedrate,
            "travel_feedrate": travel_feedrate,
            "curve_resolution": curve_resolution,
        },
        "gcode": {
            "start": start_gcode,
            "end": end_gcode,
            "lift": lift_gcode,
            "unlift": unlift_gcode,
        },
        "point": {
            "start_x": start_point.real,
            "start_y": start_point.imag,
            "max_x": max_point.real,
            "max_y": max_point.imag,
        },
    }


def test_slicing_get_dict_no_max_point():
    """Tests that turning the slicing options into a dict returns correct dict with no max point"""

    start_point = complex(1, 2)
    max_point = None
    normal_feedrate = 500
    travel_feedrate = 4000
    curve_resolution = 20
    start_gcode = ["start_gcode"]
    end_gcode = ["end_gcode"]
    lift_gcode = ["lift_gcode"]
    unlift_gcode = ["unlift_gcode"]

    options = slicing_options.SlicingOptions(
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

    assert options.get_dict() == {
        "machine": {
            "normal_feedrate": normal_feedrate,
            "travel_feedrate": travel_feedrate,
            "curve_resolution": curve_resolution,
        },
        "gcode": {
            "start": start_gcode,
            "end": end_gcode,
            "lift": lift_gcode,
            "unlift": unlift_gcode,
        },
        "point": {
            "start_x": start_point.real,
            "start_y": start_point.imag,
            "max_x": None,
            "max_y": None,
        },
    }


# endregion
# region SlicingOptionsWiget.__init__


def test_gcode_generator_inits_with_options(
    mock_slicing_options: slicing_options.SlicingOptions, qtbot: QtBot
):
    """Test that GcodeGenerator inits without error when given a options object"""

    widget = slicing_options.SlicingOptionsWiget(options=mock_slicing_options)
    qtbot.addWidget(widget)

    assert widget.options == mock_slicing_options


def test_gcode_generator_inits_with_options_file(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
):
    """Test that GcodeGenerator inits without error when given a options_file path"""
    mock_load_options: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget.load_options
    )
    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget, "load_options", mock_load_options
    )

    widget = slicing_options.SlicingOptionsWiget(options_file=pathlib.Path().cwd())
    qtbot.addWidget(widget)

    mock_load_options.assert_called_once()


def test_gcode_generator_inits_no_options(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
):
    """Test that GcodeGenerator inits without error with no options"""
    mock_load_default: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget._load_default
    )
    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget, "_load_default", mock_load_default
    )

    widget = slicing_options.SlicingOptionsWiget()
    qtbot.addWidget(widget)

    mock_load_default.assert_called_once()


# endregion
# region SlicingOptionsWiget widgets


def test_gcode_generator_creates_widgets_layouts_connection(
    mock_slicing_options: slicing_options.SlicingOptions,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that GcodeGenerator creates widgets, layout, and widget connections"""
    mock_create_widgets: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget._create_widgets
    )
    mock_create_layouts: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget._create_layouts
    )
    mock_connect_widgets: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget._connect_widgets
    )

    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget, "_create_widgets", mock_create_widgets
    )
    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget, "_create_layouts", mock_create_layouts
    )
    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget, "_connect_widgets", mock_connect_widgets
    )

    widget = slicing_options.SlicingOptionsWiget(options=mock_slicing_options)
    qtbot.addWidget(widget)

    mock_create_widgets.assert_called_once()
    mock_create_layouts.assert_called_once()
    mock_connect_widgets.assert_called_once()


def test_gcode_generator_connects_buttons_to_slots(
    mock_slicing_options: slicing_options.SlicingOptions,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that GcodeGenerator creates widgets, layout, and widget connections"""
    mock_save_options_file: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget._save_options_file
    )
    mock_load_options_file: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget._load_options_file
    )

    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget,
        "_save_options_file",
        mock_save_options_file,
    )
    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget,
        "_load_options_file",
        mock_load_options_file,
    )

    widget = slicing_options.SlicingOptionsWiget(options=mock_slicing_options)
    qtbot.addWidget(widget)

    widget.save_to_file_button.click()
    widget.load_button.click()

    mock_save_options_file.assert_called_once()
    mock_load_options_file.assert_called_once()


# endregion
# region SlicingOptionsWiget._update_option_text_fields


def test_changing_text_boxes_updates_options(
    mock_slicing_options: slicing_options.SlicingOptions, qtbot: QtBot
):
    """Tests that changing options and updating text boxes displays correct options"""
    widget = slicing_options.SlicingOptionsWiget(options=mock_slicing_options)
    qtbot.addWidget(widget)

    if not mock_slicing_options.max_point:
        mock_slicing_options.max_point = complex(1, 1)

    new_start_point = mock_slicing_options.start_point + complex(1, 1)
    new_max_point = mock_slicing_options.max_point + complex(1, 1)
    new_normal_feedrate = mock_slicing_options.normal_feedrate + 1
    new_travel_feedrate = mock_slicing_options.travel_feedrate + 1
    new_curve_resolution = mock_slicing_options.curve_resolution + 1
    new_start_gcode = list(mock_slicing_options.start_gcode) + ["new start"]
    new_end_gcode = list(mock_slicing_options.end_gcode) + ["new end"]
    new_lift_gcode = list(mock_slicing_options.lift_gcode) + ["new lift"]
    new_unlift_gcode = list(mock_slicing_options.unlift_gcode) + ["new unlift"]

    new_options = slicing_options.SlicingOptions(
        start_point=new_start_point,
        max_point=new_max_point,
        normal_feedrate=new_normal_feedrate,
        travel_feedrate=new_travel_feedrate,
        curve_resolution=new_curve_resolution,
        start_gcode=new_start_gcode,
        end_gcode=new_end_gcode,
        lift_gcode=new_lift_gcode,
        unlift_gcode=new_unlift_gcode,
    )
    widget.options = new_options
    widget._update_option_text_fields()

    assert widget.start_point_selector.spinboxes[0].spinbox.value() == int(
        new_start_point.real
    )
    assert widget.start_point_selector.spinboxes[0].spinbox.value() == int(
        new_start_point.imag
    )
    assert widget.max_point_selector.spinboxes[0].spinbox.value() == int(
        new_max_point.real
    )
    assert widget.max_point_selector.spinboxes[1].spinbox.value() == int(
        new_max_point.imag
    )
    assert widget.feedrate_selector.spinboxes[0].spinbox.value() == int(
        new_normal_feedrate
    )
    assert widget.feedrate_selector.spinboxes[1].spinbox.value() == int(
        new_travel_feedrate
    )
    assert widget.curve_resolution_spinbox.spinbox.value() == int(new_curve_resolution)
    assert widget.start_gcode_input.toPlainText() == "\n".join(new_start_gcode)
    assert widget.end_gcode_input.toPlainText() == "\n".join(new_end_gcode)
    assert widget.lift_gcode_input.toPlainText() == "\n".join(new_lift_gcode)
    assert widget.unlift_gcode_input.toPlainText() == "\n".join(new_unlift_gcode)


def test_changing_text_boxes_updates_options_no_max_point(
    mock_slicing_options: slicing_options.SlicingOptions, qtbot: QtBot
):
    """Tests that changing options and updating text boxes displays correct options"""
    widget = slicing_options.SlicingOptionsWiget(options=mock_slicing_options)
    qtbot.addWidget(widget)

    if not mock_slicing_options.max_point:
        mock_slicing_options.max_point = complex(1, 1)

    new_start_point = mock_slicing_options.start_point + complex(1, 1)
    new_max_point = None
    new_normal_feedrate = mock_slicing_options.normal_feedrate + 1
    new_travel_feedrate = mock_slicing_options.travel_feedrate + 1
    new_curve_resolution = mock_slicing_options.curve_resolution + 1
    new_start_gcode = list(mock_slicing_options.start_gcode) + ["new start"]
    new_end_gcode = list(mock_slicing_options.end_gcode) + ["new end"]
    new_lift_gcode = list(mock_slicing_options.lift_gcode) + ["new lift"]
    new_unlift_gcode = list(mock_slicing_options.unlift_gcode) + ["new unlift"]

    new_options = slicing_options.SlicingOptions(
        start_point=new_start_point,
        max_point=new_max_point,
        normal_feedrate=new_normal_feedrate,
        travel_feedrate=new_travel_feedrate,
        curve_resolution=new_curve_resolution,
        start_gcode=new_start_gcode,
        end_gcode=new_end_gcode,
        lift_gcode=new_lift_gcode,
        unlift_gcode=new_unlift_gcode,
    )
    widget.options = new_options
    widget._update_option_text_fields()

    assert widget.start_point_selector.spinboxes[0].spinbox.value() == int(
        new_start_point.real
    )
    assert widget.start_point_selector.spinboxes[0].spinbox.value() == int(
        new_start_point.imag
    )
    assert widget.max_point_selector.spinboxes[0].spinbox.value() == 0
    assert widget.max_point_selector.spinboxes[1].spinbox.value() == 0
    assert widget.feedrate_selector.spinboxes[0].spinbox.value() == int(
        new_normal_feedrate
    )
    assert widget.feedrate_selector.spinboxes[1].spinbox.value() == int(
        new_travel_feedrate
    )
    assert widget.curve_resolution_spinbox.spinbox.value() == int(new_curve_resolution)
    assert widget.start_gcode_input.toPlainText() == "\n".join(new_start_gcode)
    assert widget.end_gcode_input.toPlainText() == "\n".join(new_end_gcode)
    assert widget.lift_gcode_input.toPlainText() == "\n".join(new_lift_gcode)
    assert widget.unlift_gcode_input.toPlainText() == "\n".join(new_unlift_gcode)


# endregion
# region SlicingOptionsWiget._load_options_file


def test_loading_options_file_loads_options(
    mock_slicing_options: slicing_options.SlicingOptions,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that loading options file prompts for file selection and loads options"""
    selected_file = "somefile.toml"
    mock_select_files: mock.MagicMock = mock.create_autospec(
        helpers.select_files, return_value=(selected_file,)
    )
    monkeypatch.setattr(slicing_options.helpers, "select_files", mock_select_files)

    mock_load_options: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget.load_options
    )
    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget, "load_options", mock_load_options
    )

    widget = slicing_options.SlicingOptionsWiget(options=mock_slicing_options)
    qtbot.addWidget(widget)

    widget._load_options_file()

    mock_select_files.assert_called_once_with("TOML (*.toml)")
    mock_load_options.assert_called_once_with(widget, pathlib.Path(selected_file))


def test_loading_options_file_loads_options_no_selected_files(
    mock_slicing_options: slicing_options.SlicingOptions,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that loading options file prompts for file selection no load when no file is selected"""
    mock_select_files: mock.MagicMock = mock.create_autospec(
        helpers.select_files, return_value=[]
    )
    monkeypatch.setattr(slicing_options.helpers, "select_files", mock_select_files)

    mock_load_options: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget.load_options
    )
    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget, "load_options", mock_load_options
    )

    widget = slicing_options.SlicingOptionsWiget(options=mock_slicing_options)
    qtbot.addWidget(widget)

    widget._load_options_file()

    mock_select_files.assert_called_once_with("TOML (*.toml)")
    mock_load_options.assert_not_called()


# endregion
# region SlicingOptionsWiget._save_options_file


def test_saving_options_file_prompts_selection_of_save_file(
    mock_slicing_options: slicing_options.SlicingOptions,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
):
    """Test that saving options file prompts to save file"""
    mock_save_file: mock.MagicMock = mock.create_autospec(helpers.save_file)
    monkeypatch.setattr(slicing_options.helpers, "save_file", mock_save_file)

    widget = slicing_options.SlicingOptionsWiget(options=mock_slicing_options)
    qtbot.addWidget(widget)

    widget._save_options_file()

    mock_save_file.assert_called_once_with(
        widget, tomli_w.dumps(mock_slicing_options.get_dict()), "TOML (*.toml)"
    )


# endregion
# region SlicingOptionsWiget.load_options


@pytest.mark.parametrize(
    "normal_feedrate,travel_feedrate,curve_res,s_gcode,e_gcode,l_gcode,u_gcode,start_point,max_point",  # pylint: disable=line-too-long
    [
        (
            slicing_options.DEFAULT_NORMAL_FEEDRATE + 1,
            slicing_options.DEFAULT_TRAVEL_FEEDRATE + 1,
            slicing_options.DEFAULT_CURVE_RESOLUTION + 1,
            list(slicing_options.DEFAULT_START_GCODE) + ["start"],
            list(slicing_options.DEFAULT_END_GCODE) + ["end"],
            list(slicing_options.DEFAULT_LIFT_GCODE) + ["lift"],
            list(slicing_options.DEFAULT_UNLIFT_GCODE) + ["unlift"],
            slicing_options.DEFAULT_START_POINT + complex(1, 1),
            complex(100, 100),
        ),
        (
            None,
            slicing_options.DEFAULT_TRAVEL_FEEDRATE + 1,
            slicing_options.DEFAULT_CURVE_RESOLUTION + 1,
            list(slicing_options.DEFAULT_START_GCODE) + ["start"],
            list(slicing_options.DEFAULT_END_GCODE) + ["end"],
            list(slicing_options.DEFAULT_LIFT_GCODE) + ["lift"],
            list(slicing_options.DEFAULT_UNLIFT_GCODE) + ["unlift"],
            slicing_options.DEFAULT_START_POINT + complex(1, 1),
            complex(100, 100),
        ),
        (
            slicing_options.DEFAULT_NORMAL_FEEDRATE + 1,
            None,
            slicing_options.DEFAULT_CURVE_RESOLUTION + 1,
            list(slicing_options.DEFAULT_START_GCODE) + ["start"],
            list(slicing_options.DEFAULT_END_GCODE) + ["end"],
            list(slicing_options.DEFAULT_LIFT_GCODE) + ["lift"],
            list(slicing_options.DEFAULT_UNLIFT_GCODE) + ["unlift"],
            slicing_options.DEFAULT_START_POINT + complex(1, 1),
            complex(100, 100),
        ),
        (
            slicing_options.DEFAULT_NORMAL_FEEDRATE + 1,
            slicing_options.DEFAULT_TRAVEL_FEEDRATE + 1,
            None,
            list(slicing_options.DEFAULT_START_GCODE) + ["start"],
            list(slicing_options.DEFAULT_END_GCODE) + ["end"],
            list(slicing_options.DEFAULT_LIFT_GCODE) + ["lift"],
            list(slicing_options.DEFAULT_UNLIFT_GCODE) + ["unlift"],
            slicing_options.DEFAULT_START_POINT + complex(1, 1),
            complex(100, 100),
        ),
        (
            slicing_options.DEFAULT_NORMAL_FEEDRATE + 1,
            slicing_options.DEFAULT_TRAVEL_FEEDRATE + 1,
            slicing_options.DEFAULT_CURVE_RESOLUTION + 1,
            None,
            list(slicing_options.DEFAULT_END_GCODE) + ["end"],
            list(slicing_options.DEFAULT_LIFT_GCODE) + ["lift"],
            list(slicing_options.DEFAULT_UNLIFT_GCODE) + ["unlift"],
            slicing_options.DEFAULT_START_POINT + complex(1, 1),
            complex(100, 100),
        ),
        (
            slicing_options.DEFAULT_NORMAL_FEEDRATE + 1,
            slicing_options.DEFAULT_TRAVEL_FEEDRATE + 1,
            slicing_options.DEFAULT_CURVE_RESOLUTION + 1,
            list(slicing_options.DEFAULT_START_GCODE) + ["start"],
            None,
            list(slicing_options.DEFAULT_LIFT_GCODE) + ["lift"],
            list(slicing_options.DEFAULT_UNLIFT_GCODE) + ["unlift"],
            slicing_options.DEFAULT_START_POINT + complex(1, 1),
            complex(100, 100),
        ),
        (
            slicing_options.DEFAULT_NORMAL_FEEDRATE + 1,
            slicing_options.DEFAULT_TRAVEL_FEEDRATE + 1,
            slicing_options.DEFAULT_CURVE_RESOLUTION + 1,
            list(slicing_options.DEFAULT_START_GCODE) + ["start"],
            list(slicing_options.DEFAULT_END_GCODE) + ["end"],
            None,
            list(slicing_options.DEFAULT_UNLIFT_GCODE) + ["unlift"],
            slicing_options.DEFAULT_START_POINT + complex(1, 1),
            complex(100, 100),
        ),
        (
            slicing_options.DEFAULT_NORMAL_FEEDRATE + 1,
            slicing_options.DEFAULT_TRAVEL_FEEDRATE + 1,
            slicing_options.DEFAULT_CURVE_RESOLUTION + 1,
            list(slicing_options.DEFAULT_START_GCODE) + ["start"],
            list(slicing_options.DEFAULT_END_GCODE) + ["end"],
            list(slicing_options.DEFAULT_LIFT_GCODE) + ["lift"],
            None,
            slicing_options.DEFAULT_START_POINT + complex(1, 1),
            complex(100, 100),
        ),
        (
            slicing_options.DEFAULT_NORMAL_FEEDRATE + 1,
            slicing_options.DEFAULT_TRAVEL_FEEDRATE + 1,
            slicing_options.DEFAULT_CURVE_RESOLUTION + 1,
            list(slicing_options.DEFAULT_START_GCODE) + ["start"],
            list(slicing_options.DEFAULT_END_GCODE) + ["end"],
            list(slicing_options.DEFAULT_LIFT_GCODE) + ["lift"],
            list(slicing_options.DEFAULT_UNLIFT_GCODE) + ["unlift"],
            None,
            complex(100, 100),
        ),
        (
            slicing_options.DEFAULT_NORMAL_FEEDRATE + 1,
            slicing_options.DEFAULT_TRAVEL_FEEDRATE + 1,
            slicing_options.DEFAULT_CURVE_RESOLUTION + 1,
            list(slicing_options.DEFAULT_START_GCODE) + ["start"],
            list(slicing_options.DEFAULT_END_GCODE) + ["end"],
            list(slicing_options.DEFAULT_LIFT_GCODE) + ["lift"],
            list(slicing_options.DEFAULT_UNLIFT_GCODE) + ["unlift"],
            slicing_options.DEFAULT_START_POINT + complex(1, 1),
            None,
        ),
    ],
)
# pylint: disable=too-many-arguments
def test_loading_options_from_file(
    qtbot: QtBot,
    tmp_path: pathlib.Path,
    *,
    normal_feedrate: float | None,
    travel_feedrate: float | None,
    curve_res: int | None,
    s_gcode: list[str] | None,
    e_gcode: list[str] | None,
    l_gcode: list[str] | None,
    u_gcode: list[str] | None,
    start_point: complex | None,
    max_point: complex | None,
):
    """Test that loading options from file loads correct options"""

    data = {}
    if normal_feedrate or travel_feedrate or curve_res:
        data["machine"] = {}
    if normal_feedrate:
        data["machine"]["normal_feedrate"] = normal_feedrate
    if travel_feedrate:
        data["machine"]["travel_feedrate"] = travel_feedrate
    if curve_res:
        data["machine"]["curve_resolution"] = curve_res

    if s_gcode or e_gcode or l_gcode or u_gcode:
        data["gcode"] = {}
    if s_gcode:
        data["gcode"]["start"] = s_gcode
    if e_gcode:
        data["gcode"]["end"] = e_gcode
    if l_gcode:
        data["gcode"]["lift"] = l_gcode
    if u_gcode:
        data["gcode"]["unlift"] = u_gcode

    if start_point or max_point:
        data["point"] = {}
    if start_point:
        data["point"]["start_x"] = start_point.real
        data["point"]["start_y"] = start_point.imag
    if max_point:
        data["point"]["max_x"] = max_point.real
        data["point"]["max_y"] = max_point.imag

    toml_file = tmp_path / "temp.toml"
    with toml_file.open("wb") as f:
        tomli_w.dump(data, f)

    widget = slicing_options.SlicingOptionsWiget()
    qtbot.addWidget(widget)

    widget.load_options(toml_file)

    assert (
        widget.options.normal_feedrate == normal_feedrate
        if normal_feedrate
        else slicing_options.DEFAULT_NORMAL_FEEDRATE
    )
    assert (
        widget.options.travel_feedrate == travel_feedrate
        if travel_feedrate
        else slicing_options.DEFAULT_TRAVEL_FEEDRATE
    )
    assert (
        widget.options.curve_resolution == curve_res
        if curve_res
        else slicing_options.DEFAULT_CURVE_RESOLUTION
    )
    assert (
        widget.options.start_gcode == s_gcode
        if s_gcode
        else slicing_options.DEFAULT_START_GCODE
    )
    assert (
        widget.options.end_gcode == e_gcode
        if e_gcode
        else slicing_options.DEFAULT_END_GCODE
    )
    assert (
        widget.options.lift_gcode == l_gcode
        if l_gcode
        else slicing_options.DEFAULT_LIFT_GCODE
    )
    assert (
        widget.options.unlift_gcode == u_gcode
        if u_gcode
        else slicing_options.DEFAULT_UNLIFT_GCODE
    )
    assert (
        widget.options.start_point == start_point
        if start_point
        else slicing_options.DEFAULT_START_POINT
    )
    assert widget.options.max_point == max_point


# endregion
# region SlicingOptionsWiget._load_default


def test_loading_default_options_from_file(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
):
    """Tests that loading defaults from file updates options"""

    mock_load_options: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget.load_options
    )
    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget, "load_options", mock_load_options
    )

    widget = slicing_options.SlicingOptionsWiget()
    qtbot.addWidget(widget)

    mock_load_options.assert_called_once()


def test_loading_default_options_from_file_that_doesnt_exist(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
):
    """Tests that loading defaults from file that doesnt exist updates options to default options"""

    mock_is_file: mock.MagicMock = mock.create_autospec(
        pathlib.Path.is_file, return_value=False
    )
    monkeypatch.setattr(slicing_options.pathlib.Path, "is_file", mock_is_file)

    mock_load_options: mock.MagicMock = mock.create_autospec(
        slicing_options.SlicingOptionsWiget.load_options
    )
    monkeypatch.setattr(
        slicing_options.SlicingOptionsWiget, "load_options", mock_load_options
    )

    widget = slicing_options.SlicingOptionsWiget()
    qtbot.addWidget(widget)

    assert widget.options.start_point == slicing_options.DEFAULT_START_POINT
    assert widget.options.max_point == slicing_options.DEFAULT_MAX_POINT
    assert widget.options.normal_feedrate == slicing_options.DEFAULT_NORMAL_FEEDRATE
    assert widget.options.travel_feedrate == slicing_options.DEFAULT_TRAVEL_FEEDRATE
    assert widget.options.curve_resolution == slicing_options.DEFAULT_CURVE_RESOLUTION
    assert widget.options.blade_offset == slicing_options.DEFAULT_BLADE_OFFSET
    assert widget.options.start_gcode == slicing_options.DEFAULT_START_GCODE
    assert widget.options.end_gcode == slicing_options.DEFAULT_END_GCODE
    assert widget.options.lift_gcode == slicing_options.DEFAULT_LIFT_GCODE
    assert widget.options.unlift_gcode == slicing_options.DEFAULT_UNLIFT_GCODE

    mock_load_options.assert_not_called()


# endregion
