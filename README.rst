MIG AHB Utility Stack (MAUS) 🐭
===============================

| |Unittests status badge| |Coverage status badge| |Linting status badge| |Black status badge| |pypy status badge| |read the docs|

.. image:: https://raw.githubusercontent.com/Hochfrequenz/mig_ahb_utility_stack/main/docs/_static/maus-logo.png
   :target: https://mig-ahb-utility-stack.readthedocs.io/en/stable/api/maus.html
   :align: right
   :alt: maus logo
   :width: 150px

| This repository contains the Python package ``maus``.
| MAUS is an acronym for **M**\ IG **A**\ HB **U**\ tility **S**\ tack where MIG stands for **M**\ essage **I**\ mplementation **G**\ uide and AHB stands for **A**\ nwendungs\ **h**\ and\ **b**\ uch.
| The maus software/package allows matching single lines from the AHB with fields specified in the MIG.
| This package is necessary because EDI\@Energy does not provide any real technical and machine-readable description of the MIGs and AHBs, only PDFs.
| MAUS can also be used as a data model (``maus.model``) , without using the software or logic included in the package (MIG/AHB matching logic).

We're all hoping for the day of true digitization on which this repository will become obsolete.

What Problem Does It Solve?
---------------------------
Image you scraped the AHB PDFs into something machine-readable.
Machine-readability in this context implies, that for each field/information inside the AHB you can easily access

- segment group (e.g. "``SG4``")
- segment (e.g. "``LOC``")
- data element ID (e.g. "``3225``")
- AHB Expressions (e.g. "``Muss [123] U ([456] O [789])[904]``")

The exact data format (be it CSV, JSON, XML ...) is not important beyond an initial deserialization.

(BTW: The AHB Expression can be parsed and evaluated using the `🦅 AHBicht Library <https://github.com/Hochfrequenz/ahbicht>`__ or our AHBicht REST API which is publicly available.)

Image you also had a machine-readable version of the MIG -- spoiler: Hochfrequenz can help you with that (please contact
`@JoschaMetze <https://github.com/joschametze>`_ for a demo) -- you still weren't able to make use of your data because the MIG data and AHB data are still unrelated.
MAUS creates a connection between machine readable AHBs and machine readable MIGs.
This allows to associate certain lines from the AHB with certain fields in the MIG and is the basis for a meaningful content evaluation/validation of EDIFACT messages, or, to be more precise, validation of data structures that might be converted to EDIFACT.

Code Quality / Production Readiness
-----------------------------------

-  The code has at least a 95% unit test coverage. ✔️
-  The code is rated 10/10 in pylint and type checked with mypy (PEP 561). ✔️
-  The code is `MIT licensed <LICENSE>`__. ✔️
-  There are only `few dependencies <requirements.in>`__. ✔️

Development
-----------

Please follow the detailed instructions in the `README of our Python
Template
Repository <https://github.com/Hochfrequenz/python_template_repository#how-to-use-this-repository-on-your-machine>`__
on how to setup your local development environment (tl;dr: tox).

Contribute
----------

You are very welcome to contribute to this template repository by
opening a pull request against the main branch.

.. |Unittests status badge| image:: https://github.com/Hochfrequenz/mig_ahb_utility_stack/workflows/Unittests/badge.svg
.. |Coverage status badge| image:: https://github.com/Hochfrequenz/mig_ahb_utility_stack/workflows/Coverage/badge.svg
.. |Linting status badge| image:: https://github.com/Hochfrequenz/mig_ahb_utility_stack/workflows/Linting/badge.svg
.. |Black status badge| image:: https://github.com/Hochfrequenz/mig_ahb_utility_stack/workflows/Black/badge.svg
.. |pypy status badge| image:: https://img.shields.io/pypi/v/maus
.. |read the docs| image:: https://readthedocs.org/projects/mig-ahb-utility-stack/badge/?version=latest&style=flat
