from pathlib import Path

import pytest  # type:ignore[import]
from lxml import etree  # type:ignore[import]
from lxml.etree import Element  # type:ignore[import]

from maus.models.edifact_components import EdifactStackQuery
from maus.reader.mig_reader import MigXmlReader, check_file_can_be_parsed_as_mig_xml

ALL_MIG_XML_FILES = pytest.mark.datafiles(
    "./migs/FV2204/template_xmls/utilmd_1131.xml",
    "./migs/FV2204/template_xmls/mscons_1154.xml",
    "./migs/FV2204/template_xmls/utilmd_1154.xml",
    "./migs/FV2204/template_xmls/utilmd_2379.xml",
    "./migs/FV2204/template_xmls/utilmd_2380.xml",
    "./migs/FV2204/template_xmls/utilmd_3055.xml",
    "./migs/FV2204/template_xmls/utilmd_7402.xml",
    "./migs/FV2204/template_xmls/utilmd_3225.xml",
    "./migs/FV2204/template_xmls/utilmd_6063.xml",
    "./migs/FV2204/template_xmls/utilmd_9013.xml",
    "./migs/FV2204/template_xmls/utilmd_6411.xml",
    "./migs/FV2204/template_xmls/reqote.xml",
    "./migs/FV2210/template_xmls/utilmd_7143.xml",
)


class TestMigXmlReaderRealData:
    """
    Tests the behaviour of the Message Implementation Guide model with real world example data
    """

    @ALL_MIG_XML_FILES
    @pytest.mark.parametrize(
        "mig_xml_path, query, expected_path",
        [
            pytest.param(
                "mscons_1154.xml",
                EdifactStackQuery(
                    segment_group_key="SG1", segment_code="RFF", data_element_id="1154", name="Prüfidentifikator"
                ),
                '$["Dokument"][0]["Nachricht"][0]["Prüfidentifikator"][0]["ID"]',
                id="mscons pruefi",
            ),
            pytest.param(
                "utilmd_7402.xml",
                EdifactStackQuery(
                    segment_group_key="SG4", segment_code="IDE", data_element_id="7402", name="Vorgangsnummer"
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Vorgangsnummer"]',
                id="utilmd vorgangsnummer",
            ),
            pytest.param(
                "utilmd_2380.xml",
                EdifactStackQuery(
                    segment_group_key="root", segment_code="DTM", data_element_id="2380", name="Gültigkeit, Beginndatum"
                ),
                '$["Dokument"][0]["Nachricht"][0]["Gültigkeit,Beginndatum"]',
                id="gueltigkeit,beginndatum",
            ),
            pytest.param(
                "utilmd_2380.xml",
                EdifactStackQuery(
                    segment_group_key="SG4", segment_code="DTM", data_element_id="2380", name="Bilanzierungsbeginn"
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Bilanzierungsbeginn"]',
                id="utilmd bilanzierungsbeginn",
            ),
            pytest.param(
                "utilmd_1154.xml",
                EdifactStackQuery(
                    segment_group_key="SG6",
                    segment_code="RFF",
                    data_element_id="1154",
                    name="Referenz Vorgangsnummer(aus Anfragenachricht)",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Referenz Vorgangsnummer (aus Anfragenachricht)"][0]["Referenz"]',
                id="referenz aus anfragenachricht",
            ),
            pytest.param(
                "utilmd_1154.xml",
                EdifactStackQuery(
                    segment_group_key="SG8",
                    segment_code="RFF",
                    data_element_id="1154",
                    name="Referenz auf die ID einer Messlokation",
                    predecessor_qualifier="Z19",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Erforderliche OBIS-Daten der Messlokation"][0]["Referenz auf die ID einer Messlokation"]',
                id="referenz auf melo-id",
            ),
            pytest.param(
                "reqote.xml",
                EdifactStackQuery(
                    segment_group_key="root",
                    segment_code="DTM",
                    data_element_id="2380",
                    name="Datum oder Uhrzeit oderZeitspanne, Wert",
                    # <-- the messed up spaces are due to line breaks in the PDF
                    predecessor_qualifier="76",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Datum zum geplanten Leistungsbeginn"]',
                id="reqote lieferdatum",
            ),
            pytest.param(
                "reqote.xml",
                EdifactStackQuery(
                    segment_group_key="SG11",
                    segment_code="NAD",
                    data_element_id="3039",
                    name="MP-ID",  # <-- this used to be "Beteiligter, Identifikation"... don't know why
                    predecessor_qualifier="MS",
                ),
                '$["Dokument"][0]["Nachricht"][0]["MP-ID Absender"][0]["MP-ID"]',
                id="reqote absender",
            ),
            pytest.param(
                "reqote.xml",
                EdifactStackQuery(
                    segment_group_key="SG11",
                    segment_code="NAD",
                    data_element_id="3055",
                    name=None,
                    predecessor_qualifier="MS",
                ),
                '$["Dokument"][0]["Nachricht"][0]["MP-ID Absender"][0]["Codeliste"]',
                id="reqote absender codeliste",
            ),
            pytest.param(
                "utilmd_9013.xml",
                EdifactStackQuery(
                    segment_group_key="SG4",
                    segment_code="STS",
                    data_element_id="9013",
                    name=None,
                    predecessor_qualifier="7",
                ),
                '$["Dokument"][0]["Vorgang"][0]["Transaktionsgrund"]',
                id="UTILMD Transaktionsgrund",
            ),
            pytest.param(
                "utilmd_3225.xml",
                EdifactStackQuery(
                    segment_group_key="SG5",
                    segment_code="LOC",
                    data_element_id="3225",
                    name="Identifikator",  # <-- name in AHB != name in MIG ("ID")
                    predecessor_qualifier="172",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Meldepunkt"][0]["ID"]',
                id="UTILMD: LOC ID vs. Identifikator",
            ),
            pytest.param(
                "utilmd_1154.xml",
                EdifactStackQuery(
                    segment_group_key="SG6",
                    segment_code="RFF",  # this is a reference
                    data_element_id="1154",
                    name="ID der Marktlokation",  # <-- name in AHB != name in MIG ("ID")
                    predecessor_qualifier="Z18",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Referenz auf die ID der Marktlokation für Termine der Marktlokation"][0]["ID"]',
                id="UTILMD: LOC ID der MaLo Z18",
            ),
            pytest.param(
                "utilmd_2380.xml",
                EdifactStackQuery(
                    segment_group_key="SG6",
                    segment_code="DTM",
                    data_element_id="2380",
                    name="Datum oder Uhrzeit oderZeitspanne, Wert",
                    predecessor_qualifier="752",
                    section_name="Geplante Turnusablesung des MSB (Strom)"
                    # division=Division.ELECTRICITY,
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Geplante Turnusablesung des MSB (Strom)"]',
                id="UTILMD geplante Turnusablesung 752",
            ),
            pytest.param(
                "reqote.xml",
                EdifactStackQuery(
                    segment_group_key="SG11",
                    segment_code="NAD",
                    data_element_id="3055",
                    name=None,
                    predecessor_qualifier=None,
                    section_name="MP-ID Absender"
                    # division=Division.ELECTRICITY,
                ),
                '$["Dokument"][0]["Nachricht"][0]["MP-ID Absender"][0]["Codeliste"]',
                id="REQOTE Absender",
            ),
            pytest.param(
                "utilmd_6063.xml",
                EdifactStackQuery(
                    segment_group_key="SG9",
                    segment_code="QTY",
                    data_element_id="6063",
                    name=None,
                    predecessor_qualifier="Z01",
                    section_name="Arbeit / Leistung für tagesparameterabhängige Marktlokation",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Daten der Marktlokation"][0]["Arbeit / Leistung für tagesparameterabhängige Marktlokation"][0]["Qualifier"]',
                id="UTILMD 6063",
            ),
            pytest.param(
                "utilmd_1131.xml",
                EdifactStackQuery(
                    segment_group_key="SG10",
                    segment_code="CCI",
                    data_element_id="1131",
                    name=None,
                    predecessor_qualifier="Z17",
                    section_name="Fallgruppenzuordnung",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Daten der Marktlokation"][0]["Fallgruppenzuordnung"][0]["Zuordnung"]',
                id="UTILMD 1131 (Fallgruppenzuordnung)",
            ),
            pytest.param(
                "utilmd_3055.xml",
                EdifactStackQuery(
                    segment_group_key="SG12",
                    segment_code="NAD",
                    data_element_id="3055",
                    name=None,
                    predecessor_qualifier=None,
                    section_name="Beteiligter Marktpartner MP- ID",  # note that the "MP- ID" contains a space
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Beteiligter Marktpartner MP-ID"][0]["Codeliste"]',
                id="UTILMD 3055, Beteiligter Marktpartner",
            ),
            pytest.param(
                "utilmd_6411.xml",
                EdifactStackQuery(
                    segment_group_key="SG9",
                    segment_code="QTY",
                    data_element_id="6411",
                    name=None,
                    predecessor_qualifier="Z01",  # from parents parent
                    section_name="Arbeit / Leistung für tagesparameterabhängige Marktlokation",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Daten der Marktlokation"][0]["Arbeit / Leistung für tagesparameterabhängige Marktlokation"][0]["Maßeinheit"]',
                id="UTILMD 6411, Beteiligter Marktpartner",
            ),
            pytest.param(
                "utilmd_7143.xml",
                EdifactStackQuery(
                    segment_group_key="SG8",
                    segment_code="PIA",
                    data_element_id="7143",
                    name=None,
                    predecessor_qualifier="Z45",  # <-- important is, that this is Z45 and not Z02
                    section_name="Gruppenartikel-ID / Artikel- ID",
                ),
                '$["Dokument"][0]["Nachricht"][0]["Vorgang"][0]["Netznutzungsabrechnungsdaten der Marktlokation"][0]["Gruppenartikel-ID / Artikel-ID"][0]["Art der ID"]',
                id="UTILMD 7143, (Gruppen)ArtikelId",
            )
            # pytest.param( # unsolved
            #    "utilmd_1154.xml",
            # EdifactStackQuery(segment_group_key='SG8', segment_code='RFF', data_element_id='1154',
            #                  name='ID der Marktlokation', predecessor_qualifier='Z18',
            #                  section_name='Referenz auf die ID der Marktlokation'),
            #    '$["Dokument"][0]["Vorgang"]["0"]["Daten der Marktlokation"][0]["Referenz auf die ID der Marktlokation"]',
            #    id="Referenz auf die ID der Marktlokation"
            # )
            # pytest.param( # unsolved
            #    "utilmd_2379.xml",
            #    EdifactStackQuery(
            #        segment_group_key="SG6",
            #        segment_code="DTM",
            #        data_element_id="2379",
            #        name=None,
            #        predecessor_qualifier="752",
            #        section_name="Geplante Turnusablesung des MSB (Strom)",
            #    ),
            #    "$['foo']",
            #    id="UTILMD geplante Turnusablesung (Qualifier)",
            #    # https://github.com/Hochfrequenz/edifact-templates/issues/24
            # ),
        ],
    )
    def test_simple_paths(
        self,
        datafiles,
        mig_xml_path: str,
        query: EdifactStackQuery,
        expected_path: str,
    ):
        reader = MigXmlReader(Path(datafiles) / mig_xml_path)
        actual_stack = reader.get_edifact_stack(query)
        assert actual_stack is not None
        assert actual_stack.to_json_path() == expected_path  # type:ignore[union-attr]

    @ALL_MIG_XML_FILES
    def test_is_parsable(self, datafiles):
        check_file_can_be_parsed_as_mig_xml(Path(datafiles) / Path("utilmd_3225.xml"))
        # if no exception is thrown, the test is successful
