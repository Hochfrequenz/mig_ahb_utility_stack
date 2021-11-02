from src.maus.maus import AhbLine, Anwendungshandbuch, MessageImplementationGuide, MigAhbUtilityStack


class TestMigAhbMatcher:
    """
    A class with pytest unit tests.
    """

    def test_something(self):
        utilmd_mig = MessageImplementationGuide(
            mig_json=[
                {
                    "key": "Dokument",
                    "requires": [
                        {
                            "Dokument": [
                                {
                                    "key": "Nachricht",
                                    "_meta": {
                                        "type": "group",
                                        "max": "9999",
                                        "groupKey": "Nachrichten-Referenznummer",
                                        "sg": "UNH",
                                    },
                                    "requires": [
                                        {
                                            "Nachricht": [
                                                {
                                                    "key": "Vorgang",
                                                    "_meta": {
                                                        "type": "group",
                                                        "max": "99999",
                                                        "groupKey": "Vorgangsnummer",
                                                        "sg": "SG4",
                                                    },
                                                    "requires": [
                                                        {
                                                            "Vorgang": [
                                                                {
                                                                    "key": "Meldepunkt",
                                                                    "_meta": {
                                                                        "type": "group",
                                                                        "objType": "Meldepunkte",
                                                                        "changeTrigger": "trigger_meldepunkt_change",
                                                                        "max": "999999",
                                                                        "groupKey": "ID",
                                                                        "sg": "SG5",
                                                                    },
                                                                    "requires": [
                                                                        {
                                                                            "Meldepunkt": [
                                                                                {
                                                                                    "ID": "ID",
                                                                                    "_meta": {
                                                                                        "id": "3225",
                                                                                        "sg": "SG5",
                                                                                        "segment": "LOC",
                                                                                        "typeInfo": "an",
                                                                                        "length": 35,
                                                                                    },
                                                                                }
                                                                            ]
                                                                        }
                                                                    ],
                                                                }
                                                            ]
                                                        }
                                                    ],
                                                }
                                            ]
                                        }
                                    ],
                                }
                            ]
                        }
                    ],
                }
            ]
        )

        meldepunkt_id = AhbLine(
            segment_group="SG5", segment="LOC", data_element="3225", name="Identifikator", ahb_expression="X [953]"
        )
        wim_ahb = Anwendungshandbuch(lines=[meldepunkt_id], pruefidentifikator="11042")
        maus = MigAhbUtilityStack(ahb=wim_ahb, mig=utilmd_mig)

        assert maus is not None
