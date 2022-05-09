from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestAnmeldungMaus:
    """
    A unit test that ensures that the 11001/11002/11003 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11001.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11001(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11001.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11001_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11002.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11002(self, datafiles):
        result = create_maus_and_assert(
            csv_path=Path(datafiles) / "11002.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11002_maus.json"),
        )
        nav_segments = result.maus.find_segments(
            group_predicate=lambda group: group.discriminator == "SG10",
            segment_predicate=lambda seg: seg.discriminator == "CAV"
            and seg.section_name == "Netznutzungsabrechnungsvariante",
        )
        assert len(nav_segments) == 1  # https://github.com/Hochfrequenz/edifact-templates/issues/73
        for expected_section_name, unexpected_section_name in [
            (
                # https://github.com/Hochfrequenz/edifact-templates/issues/82
                "OBIS-Kennzahl der Zähleinrichtung / Mengenumwerter",
                "OBIS-Kennzahl der Zähleinrichtung / Mengenumwerter / Smartmeter-Gateway",
            ),
            (
                # https://github.com/Hochfrequenz/edifact-templates/issues/82
                "OBIS-Daten der Zähleinrichtung / Mengenumwerter",
                "OBIS-Daten der Zähleinrichtung / Mengenumwerter / Smartmeter-Gateway",
            ),
        ]:
            expected_zaehleinrichtungs_obis = result.maus.find_segments(
                segment_predicate=lambda seg: seg.section_name == expected_section_name
            )
            assert len(expected_zaehleinrichtungs_obis) > 0
            unexpected_zaehleinrichtungs_obis = result.maus.find_segments(
                segment_predicate=lambda seg: seg.section_name == unexpected_section_name
            )
            assert len(unexpected_zaehleinrichtungs_obis) == 0
        assert (
            len(
                result.maus.find_segments(
                    segment_predicate=lambda seg: seg.discriminator == "SEQ"
                    and seg.section_name == "OBIS-Daten der Marktlokation",
                )
            )
            > 0
        )  # https://github.com/Hochfrequenz/edifact-templates/issues/81
        assert (
            len(
                result.maus.find_segments(
                    segment_predicate=lambda seg: seg.discriminator == "CAV"
                    and seg.section_name == "Druckebene der Marktlokation",
                )
            )
            > 0
        )  # https://github.com/Hochfrequenz/edifact-templates/issues/79

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2c.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2110/UTILMD/11003.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11003(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11003.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2110/UTILMD/11003_maus.json"),
        )
