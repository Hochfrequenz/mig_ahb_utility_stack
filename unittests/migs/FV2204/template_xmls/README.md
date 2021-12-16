## Template XML Files

Internally Hochfrequenz uses an XML based representation to describe order and structure of segments and groups inside an EDIFACT message.
These XML files are the basis for further transformations to/from EDIFACT.

Creating said XML files was enormous amount of work, that's why they are not publicly available in this repository.
This folder contains only minimal working examples that are used for the unittests.

As written in the main README, we're all hoping for EDI@Energy to live modern standards and publish technical documentation in an appropriate machine-readable format, not PDFs.
Please contact [@JoschaMetze](https://github.com/joschametze) if you're interested in an EDIFACT ↔ `X` mapping where `X` can be basically anything from purely technical transformations into/from XML or JSON but also functional mapping into standards like e.g. [BO4E](https://github.com/topics/bo4e).
