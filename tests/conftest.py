"""
Common test fixtures
"""

import pytest

from svg_slicer import slicing_options


@pytest.fixture()
def mock_slicing_options() -> slicing_options.SlicingOptions:
    """Fixture for slicing options"""
    return slicing_options.SlicingOptions(
        start_point=complex(0, 0),
        max_point=complex(10, 10),
        normal_feedrate=500,
        travel_feedrate=1000,
        curve_resolution=10,
        start_gcode=["; start"],
        end_gcode=["; end"],
        lift_gcode=["G1 Z10"],
        unlift_gcode=["G1 Z0"],
    )
