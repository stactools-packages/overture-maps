from pathlib import Path

from click import Group
from click.testing import CliRunner
from pystac import Collection, Item

from stactools.overture_maps.commands import create_overturemaps_command

command = create_overturemaps_command(Group())


def test_create_collection(tmp_path: Path) -> None:
    # Smoke test for the command line create-collection command
    #
    # Most checks should be done in test_stac.py::test_create_collection

    path = str(tmp_path / "collection.json")
    runner = CliRunner()
    result = runner.invoke(
        command, ["create-collection", "buildings", "azure", "2024-12-18.0", path]
    )
    assert result.exit_code == 0, "\n{}".format(result.output)
    collection = Collection.from_file(path)
    collection.validate()


def test_create_item(tmp_path: Path) -> None:
    # Smoke test for the command line create-item command
    #
    # Most checks should be done in test_stac.py::test_create_item
    path = str(tmp_path / "item.json")
    runner = CliRunner()
    result = runner.invoke(
        command,
        [
            "create-item",
            "https://overturemapswestus2.blob.core.windows.net/release/2024-12-18.0/theme=addresses/type=address/part-00000-de803747-d78d-4060-b3da-da6dcd5dbab8-c000.zstd.parquet",
            path,
        ],
    )
    assert result.exit_code == 0, "\n{}".format(result.output)
    item = Item.from_file(path)
    item.validate()
