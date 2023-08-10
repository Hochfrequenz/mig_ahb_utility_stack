"""
the maus cli tool
"""
import json
from pathlib import Path

import click

from maus.mig_ahb_matching import to_deep_ahb
from maus.models.anwendungshandbuch import (
    DeepAnwendungshandbuch,
    DeepAnwendungshandbuchSchema,
    FlatAnwendungshandbuchSchema,
)
from maus.models.message_implementation_guide import SegmentGroupHierarchySchema
from maus.reader.mig_xml_reader import MigXmlReader


# pylint:disable=too-many-arguments
@click.command()
@click.version_option()
@click.option(
    "-fap",
    "--flat_ahb_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to the flat ahb json file",
    required=True,
)
@click.option(
    "-sghp",
    "--sgh_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to the sgh json file",
    required=True,
)
@click.option(
    "-tp",
    "--template_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to the template file",
    required=True,
)
@click.option(
    "-cp",
    "--check_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to the maus json file",
)
@click.option(
    "-o",
    "--output_path",
    type=click.Path(dir_okay=False, file_okay=True, path_type=Path),
    help="Path to the output file",
)
# pylint:disable=no-value-for-parameter
def main(
    flat_ahb_path: Path,
    sgh_path: Path,
    template_path: Path,
    check_path: Path,
    output_path: Path,
):
    """
    🐭 MAUS CLI is a standalone executable that generates .maus.json files from given input data
    """

    if check_path is None and output_path is None or check_path is not None and output_path is not None:
        # pylint:disable=line-too-long
        click.secho(
            "❌ You need to specify either the `output_path` or the `check_path` parameter. Please use --help to see more information.",
            fg="red",
        )
        raise click.Abort()

    with open(flat_ahb_path, "r", encoding="utf-8") as flat_ahb_file:
        flat_ahb = FlatAnwendungshandbuchSchema().load(json.load(flat_ahb_file))
    with open(sgh_path, "r", encoding="utf-8") as sgh_file:
        sgh = SegmentGroupHierarchySchema().loads(sgh_file.read())

    mig_reader = MigXmlReader(template_path)

    # create new maus.json files
    maus = to_deep_ahb(flat_ahb, sgh, mig_reader)

    if output_path is not None and check_path is not None:
        click.secho("❌ You can only specify one of the output_path and maus_to_check_path parameters", fg="red")
        raise click.Abort()

    if output_path is not None:
        maus_dict = DeepAnwendungshandbuchSchema().dump(maus)

        with open(output_path, "w", encoding="utf-8") as maus_file:
            json.dump(maus_dict, maus_file, indent=2, ensure_ascii=False, sort_keys=True)

    if check_path is not None:
        with open(check_path, "r", encoding="utf-8") as maus_file:
            expected_maus: DeepAnwendungshandbuch = DeepAnwendungshandbuchSchema().loads(maus_file.read())

            # reset the line index to make the comparison work
            # this is fine cause there is no logic built on top of the line index
            maus.reset_ahb_line_index()
            expected_maus.reset_ahb_line_index()

            if expected_maus == maus:
                click.secho("✅ The generated maus.json matches the expected one", fg="green")
            else:
                click.secho("❌ The generated maus.json does not match the expected one!", fg="red")
                raise click.Abort()


if __name__ == "__main__":
    main()  # pylint:disable=no-value-for-parameter
