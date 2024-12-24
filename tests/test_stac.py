import os

import pytest

from stactools.overture_maps import stac
from stactools.overture_maps.constants import AZURE_NETLOC

asset_path = "release/2024-12-18.0/theme=buildings/type=building/part-00000-35685b01-5d46-4cb5-8449-5b27bcbfe445-c000.zstd.parquet"
test_dir = os.path.dirname(os.path.abspath(__file__))


def test_create_collection() -> None:
    # This function should be updated to exercise the attributes of interest on
    # the collection

    collection = stac.create_collection()
    collection.set_self_href(None)  # required for validation to pass
    assert collection.id == "example-collection"
    assert collection.extra_fields["custom_attribute"] == "foo"
    collection.validate()


@pytest.mark.parametrize(
    "href",
    [
        f"file://{test_dir}/data/{asset_path}",
        "s3://overturemaps-us-west-2/release/2024-12-18.0/theme=buildings/type=building/part-00000-2a7085d3-4cd8-40f2-adaf-0c6d59a3b7d9-c000.zstd.parquet",
        f"https://{AZURE_NETLOC}/{asset_path}",
    ],
)
def test_create_item(href: str) -> None:
    # This function should be updated to exercise the attributes of interest on
    # a typical item

    item = stac.create_item(href)
    item.validate()
