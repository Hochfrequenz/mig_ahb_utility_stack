"""
maus is the MIG AHB Utility Stack
"""
import json
from pathlib import Path

import click

from maus.mig_ahb_matching import to_deep_ahb
from maus.models.anwendungshandbuch import DeepAnwendungshandbuchSchema, FlatAnwendungshandbuchSchema
from maus.models.message_implementation_guide import SegmentGroupHierarchySchema
from maus.reader.mig_xml_reader import MigXmlReader


# pylint:disable=too-many-arguments
@click.command()
@click.version_option()
@click.option(
    "-fap", "--flat_ahb_path", type=click.Path(exists=True, path_type=Path), help="Path to the flat ahb json file"
)
@click.option("-sghp", "--sgh_path", type=click.Path(exists=True, path_type=Path), help="Path to the sgh json file")
@click.option("-tp", "--template_path", type=click.Path(exists=True, path_type=Path), help="Path to the template file")
@click.option("-cp", "--check_path", type=click.Path(exists=True, path_type=Path), help="Path to the maus json file")
@click.option(
    "-o",
    "--output_path",
    type=click.Path(dir_okay=False, file_okay=True, path_type=Path),
    help="Path to the output file",
)
@click.option("-v", "--verbose", is_flag=True, help="Print additional information")
def main(
    flat_ahb_path: Path,
    sgh_path: Path,
    template_path: Path,
    check_path: Path,
    output_path: Path,
    verbose: bool,
):
    """
    The main entry point for the maus command line interface
    """

    with open(flat_ahb_path, "r", encoding="utf-8") as flat_ahb_file:
        flat_ahb = FlatAnwendungshandbuchSchema().load(json.load(flat_ahb_file))
    with open(sgh_path, "r", encoding="utf-8") as sgh_file:
        sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())

    mig_reader = MigXmlReader(template_path)

    # create new maus.json files
    maus = to_deep_ahb(flat_ahb, sgh, mig_reader)

    if output_path is not None and check_path is not None:
        raise Exception("You can only specify one of the output_path and maus_to_check_path parameters")

    if output_path is not None:
        maus_dict = DeepAnwendungshandbuchSchema().dump(maus)

        with open(output_path, "w", encoding="utf-8") as maus_file:
            json.dump(maus_dict, maus_file, indent=2, ensure_ascii=False, sort_keys=True)

    if check_path is not None:
        with open(check_path, "r", encoding="utf-8") as maus_file:
            expected_maus = DeepAnwendungshandbuchSchema().loads(maus_file.read())

            if expected_maus == maus:
                click.secho("✅ The generated maus.json matches the expected one", fg="green")
            else:
                click.secho("❌ The generated maus.json does not match the expected one!", fg="red")
                raise click.Abort()


if __name__ == "__main__":
    main()
