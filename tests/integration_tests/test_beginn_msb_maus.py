from pathlib import Path

import pytest  # type:ignore[import]
from helpers import create_maus_and_assert, write_to_file_or_assert_equality  # type:ignore[import]


class TestBeginnMsbMaus:
    """
    A unit test that ensures that the 11042/43/44 MAUS.json are created.
    """

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11042.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11042_52e(self, datafiles):
        result = create_maus_and_assert(
            csv_path=Path(datafiles) / "11042.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11042_maus.json"),
        )
        kunde_des_msb_segments = result.maus.find_segments(
            group_predicate=lambda group: group.discriminator == "SG12",
            segment_predicate=lambda seg: seg.discriminator == "NAD"
            and seg.section_name == "Kunde des Messstellenbetreibers",
        )
        assert len(kunde_des_msb_segments) == 1
        nad_de_discriminators = [de.discriminator for de in kunde_des_msb_segments[0].data_elements]
        assert (
            '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Kunde des Messstellenbetreibers"][0]["Name des Beteiligten"]'
            in nad_de_discriminators
        )
        assert (
            '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Kunde des Messstellenbetreibers"][0]["Struktur"]'
            in nad_de_discriminators
        )
        korrespondenz_des_msb_kunden = result.maus.find_segments(
            group_predicate=lambda group: group.discriminator == "SG12",
            segment_predicate=lambda seg: seg.discriminator == "NAD"
            and seg.section_name == "Korrespondenzanschrift des Kunden des Messstellenbetreibers",
        )
        assert len(korrespondenz_des_msb_kunden) == 1
        nad_de_discriminators = [de.discriminator for de in korrespondenz_des_msb_kunden[0].data_elements]
        assert (
            '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Korrespondenzanschrift des Kunden des Messstellenbetreibers"][0]["Name des Beteiligten"]'
            in nad_de_discriminators
        )
        assert (
            '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Korrespondenzanschrift des Kunden des Messstellenbetreibers"][0]["Struktur"]'
            in nad_de_discriminators
        )
        assert (
            '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Korrespondenzanschrift des Kunden des Messstellenbetreibers"][0]["Strasse und Hausnummer oder Postfach"]'
            in nad_de_discriminators
        )
        assert (
            '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Korrespondenzanschrift des Kunden des Messstellenbetreibers"][0]["Ort"]'
            in nad_de_discriminators
        )
        assert (
            '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Korrespondenzanschrift des Kunden des Messstellenbetreibers"][0]["Postleitzahl"]'
            in nad_de_discriminators
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11043.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11043(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11043.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11043_maus.json"),
        )

    @pytest.mark.datafiles("./edifact-templates/edi/UTILMD/UTILMD5.2e.template")
    @pytest.mark.datafiles("./edifact-templates/ahbs/FV2210/UTILMD/11044.csv")
    @pytest.mark.datafiles("../unit_tests/migs/FV2204/segment_group_hierarchies/sgh_utilmd.json")
    def test_maus_creation_11044(self, datafiles):
        create_maus_and_assert(
            csv_path=Path(datafiles) / "11044.csv",
            sgh_path=Path(datafiles) / "sgh_utilmd.json",
            template_path=Path(datafiles) / Path("UTILMD5.2c.template"),
            maus_path=Path("edifact-templates/maus/FV2210/UTILMD/11044_maus.json"),
        )
