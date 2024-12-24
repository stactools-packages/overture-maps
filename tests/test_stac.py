import os
import re

import pytest

from stactools.overture_maps import stac
from stactools.overture_maps.constants import COLLECTION_ID_FORMAT
from stactools.overture_maps.metadata import StorageBackend, Theme

LATEST_RELEASE = "2024-12-18.0"
AZURE_PREFIX = "https://overturemapswestus2.blob.core.windows.net/release/2024-12-18.0"
asset_path = ""
test_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize("theme", list(Theme))  # type: ignore
@pytest.mark.parametrize("storage_backend", list(StorageBackend))  # type: ignore
def test_create_collection(theme: Theme, storage_backend: StorageBackend) -> None:
    # This function should be updated to exercise the attributes of interest on
    # the collection

    collection = stac.create_collection(
        theme=theme, storage_backend=storage_backend, latest_release=LATEST_RELEASE
    )
    collection.set_self_href(None)  # required for validation to pass

    assert collection.id == COLLECTION_ID_FORMAT.format(theme=theme.value)
    assert collection.extra_fields["overture:theme"] == theme.value
    collection.validate()


@pytest.mark.vcr  # type: ignore
@pytest.mark.parametrize(
    "href",
    [
        f"{AZURE_PREFIX}/theme=addresses/type=address/part-00000-de803747-d78d-4060-b3da-da6dcd5dbab8-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=buildings/type=building/part-00000-35685b01-5d46-4cb5-8449-5b27bcbfe445-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=buildings/type=building_part/part-00000-ecfd20fa-cba1-430d-979d-d75b6d5ef6b2-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=divisions/type=division/part-00000-0e64b561-1627-4112-99b8-f0e3b4d54916-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=divisions/type=division_area/part-00000-3bc3de71-0151-4d7b-b6b6-cf1605c75656-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=divisions/type=division_boundary/part-00000-58d6e82c-f48c-409d-aa36-8581465d6b8f-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=places/type=place/part-00000-13a6583b-537c-465b-81c3-1b27da7ea22b-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=transportation/type=segment/part-00000-197fe3eb-5952-413d-99fe-44cdb1365072-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=transportation/type=connector/part-00000-e54d988e-e80b-48dc-8b04-01bdab3f0f84-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=base/type=bathymetry/part-00000-525e3c93-96a6-4a98-800c-c775a78ee1c4-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=base/type=infrastructure/part-00000-39d9bb03-cbe8-4be7-ae7e-1950c21757a4-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=base/type=land/part-00000-4abc29a3-e0c9-4f11-bab4-53e38b9f6c5d-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=base/type=land_cover/part-00000-3afdb121-7f1d-4381-97fe-cc4e2c239a59-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=base/type=land_use/part-00000-bf2c0901-35f5-4961-a008-2e76f665d4cf-c000.zstd.parquet",
        f"{AZURE_PREFIX}/theme=base/type=water/part-00000-a218524c-21b4-4716-9b1f-fa43547d95a3-c000.zstd.parquet",
    ],
)  # type: ignore
def test_create_item(href: str) -> None:
    pattern = r"theme=([^/]+)/type=([^/]+)/"
    match = re.search(pattern, href)

    if not match:
        raise ValueError(f"Could not extract theme and type from href: {href}")

    theme, feature_type = match.groups()

    item = stac.create_item(href)
    assert item.properties["overture:theme"] == theme
    assert item.properties["overture:type"] == feature_type
    item.validate()
