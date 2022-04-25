# Integration Tests

The scope of the integration tests is to test the integration of multiple components of MAUS.

The data on which the integration tests rely on are completely digitized MIGs and AHBs which are *not* publicly available.
These are embedded as a private git submodule: [Hochfrequenz/edifact-templates](edifact-templates).

The integrations tests are encapsulated in their own package and own tox testing environment.
They'll also run in a CI step/Github Action.
