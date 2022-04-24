from typing import List, Optional, Tuple

import pytest  # type:ignore[import]

from maus.models.message_implementation_guide import SegmentGroupHierarchy, SegmentGroupHierarchySchema
from unit_tests.serialization_test_helper import assert_serialization_roundtrip  # type:ignore[import]

ALL_SGH_FILES = pytest.mark.datafiles(
    "./unit_tests/migs/FV2204/segment_group_hierarchies/sgh_mscons.json",
    "./unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json",
    "./unit_tests/migs/FV2204/segment_group_hierarchies/sgh_reqote.json",
    "./unit_tests/migs/FV2204/segment_group_hierarchies/sgh_iftsta.json",
)


class TestMig:
    """
    Tests the behaviour of the Message Implementation Guide model
    """

    @pytest.mark.parametrize(
        "sgh, expected_json_dict",
        [
            pytest.param(
                # this is basically UTILMD as of FV2204
                SegmentGroupHierarchy(
                    segment_group=None,
                    opening_segment="UNH",
                    sub_hierarchy=[
                        SegmentGroupHierarchy(segment_group="SG1", opening_segment="RFF", sub_hierarchy=[]),
                        SegmentGroupHierarchy(
                            segment_group="SG2",
                            opening_segment="NAD",
                            sub_hierarchy=[
                                SegmentGroupHierarchy(segment_group="SG3", opening_segment="CTA", sub_hierarchy=[])
                            ],
                        ),
                        SegmentGroupHierarchy(
                            segment_group="SG4",
                            opening_segment="IDE",
                            sub_hierarchy=[
                                SegmentGroupHierarchy(
                                    segment_group="SG5",
                                    opening_segment="LOC",
                                    sub_hierarchy=None,
                                ),
                                SegmentGroupHierarchy(segment_group="SG6", opening_segment="RFF", sub_hierarchy=None),
                                SegmentGroupHierarchy(
                                    segment_group="SG8",
                                    opening_segment="SEQ",
                                    sub_hierarchy=[
                                        SegmentGroupHierarchy(
                                            segment_group="SG9", opening_segment="QTY", sub_hierarchy=None
                                        ),
                                        SegmentGroupHierarchy(
                                            segment_group="SG10", opening_segment="CCI", sub_hierarchy=None
                                        ),
                                    ],
                                ),
                                SegmentGroupHierarchy(segment_group="SG12", opening_segment="NAD", sub_hierarchy=None),
                            ],
                        ),
                    ],
                ),
                {
                    "opening_segment": "UNH",
                    "segment_group": None,
                    "sub_hierarchy": [
                        {"opening_segment": "RFF", "segment_group": "SG1", "sub_hierarchy": []},
                        {
                            "opening_segment": "NAD",
                            "segment_group": "SG2",
                            "sub_hierarchy": [{"opening_segment": "CTA", "segment_group": "SG3", "sub_hierarchy": []}],
                        },
                        {
                            "opening_segment": "IDE",
                            "segment_group": "SG4",
                            "sub_hierarchy": [
                                {"opening_segment": "LOC", "segment_group": "SG5", "sub_hierarchy": None},
                                {"opening_segment": "RFF", "segment_group": "SG6", "sub_hierarchy": None},
                                {
                                    "opening_segment": "SEQ",
                                    "segment_group": "SG8",
                                    "sub_hierarchy": [
                                        {"opening_segment": "QTY", "segment_group": "SG9", "sub_hierarchy": None},
                                        {"opening_segment": "CCI", "segment_group": "SG10", "sub_hierarchy": None},
                                    ],
                                },
                                {"opening_segment": "NAD", "segment_group": "SG12", "sub_hierarchy": None},
                            ],
                        },
                    ],
                },
                id="UTILMD",
            ),
        ],
    )
    def test_segment_group_hierarchy_serialization_roundtrip(
        self, sgh: SegmentGroupHierarchy, expected_json_dict: dict
    ):
        assert_serialization_roundtrip(sgh, SegmentGroupHierarchySchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "sgh_file_path, expected_flattened",
        [
            pytest.param(
                "sgh_utilmd.json",
                [
                    (None, "UNH"),
                    ("SG1", "RFF"),
                    ("SG2", "NAD"),
                    ("SG3", "CTA"),
                    ("SG4", "IDE"),
                    ("SG5", "LOC"),
                    ("SG6", "RFF"),
                    ("SG8", "SEQ"),
                    ("SG9", "QTY"),
                    ("SG10", "CCI"),
                    ("SG12", "NAD"),
                ],
            ),
            pytest.param(
                "sgh_mscons.json",
                [
                    (None, "UNB"),
                    ("SG1", "RFF"),
                    ("SG2", "NAD"),
                    ("SG4", "CTA"),
                    ("SG5", "NAD"),
                    ("SG6", "LOC"),
                    ("SG7", "RFF"),
                    ("SG8", "CCI"),
                    ("SG9", "LIN"),
                    ("SG10", "QTY"),
                ],
            ),
            pytest.param(
                "sgh_reqote.json",
                [
                    (None, "UNH"),
                    ("SG1", "RFF"),
                    ("SG11", "NAD"),
                    ("SG14", "CTA"),
                    ("SG27", "LIN"),
                ],
            ),
        ],
    )
    @ALL_SGH_FILES
    def test_flattening(self, datafiles, sgh_file_path: str, expected_flattened: List[Tuple[Optional[str], str]]):
        with open(datafiles / sgh_file_path, "r", encoding="utf-8") as sgh_file:
            sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())
        actual = sgh.flattened()
        assert actual == expected_flattened

    @pytest.mark.parametrize(
        "sgh",
        [
            pytest.param(
                SegmentGroupHierarchy(
                    segment_group="SG4",
                    opening_segment="IDE",
                    sub_hierarchy=[
                        SegmentGroupHierarchy(
                            segment_group="SG5",
                            opening_segment="LOC",
                            sub_hierarchy=None,
                        ),
                        SegmentGroupHierarchy(segment_group="SG6", opening_segment="RFF", sub_hierarchy=None),
                        SegmentGroupHierarchy(
                            segment_group="SG8",
                            opening_segment="SEQ",
                            sub_hierarchy=[
                                SegmentGroupHierarchy(segment_group="SG9", opening_segment="QTY", sub_hierarchy=None),
                                SegmentGroupHierarchy(segment_group="SG10", opening_segment="CCI", sub_hierarchy=None),
                            ],
                        ),
                        SegmentGroupHierarchy(segment_group="SG12", opening_segment="NAD", sub_hierarchy=None),
                    ],
                ),
                id="UTILMD SG4",
            )
        ],
    )
    @pytest.mark.parametrize(
        "sg_key, expected_is_below",
        [
            pytest.param("SG5", True, id="first level below, first entry"),
            pytest.param("SG8", True, id="first level below, third entry"),
            pytest.param("SG9", True, id="second level below, first entry"),
            pytest.param("SG10", True, id="second level below, second entry"),
            pytest.param("SG2", False, id="does not exist (is above)"),
            pytest.param("SG4", False, id="itself is not below"),
            pytest.param(None, False, id="None is above SG4 (not shown)"),
        ],
    )
    def test_is_hierarchically_below(self, sgh: SegmentGroupHierarchy, sg_key: Optional[str], expected_is_below: bool):
        actual = sgh.is_hierarchically_below(sg_key)
        assert actual == expected_is_below
