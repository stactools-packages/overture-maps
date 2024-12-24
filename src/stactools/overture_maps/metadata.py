import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Union
from urllib.parse import urlparse

import httpx
import pyarrow.parquet as pq
from adlfs import AzureBlobFileSystem
from geojson_pydantic import Polygon
from parse import Result, parse
from pystac import (
    Asset,
    Collection,
    Extent,
    Item,
    Link,
    MediaType,
    Provider,
    ProviderRole,
    RelType,
    SpatialExtent,
    TemporalExtent,
)
from pystac.extensions import table
from pystac.extensions.item_assets import AssetDefinition, ItemAssetsExtension
from pystac.extensions.version import VersionExtension
from s3fs import S3FileSystem

from stactools.overture_maps.constants import (
    AZURE_NETLOC,
    COLLECTION_ID_FORMAT,
    FIRST_RELEASE_DATE,
    ODBL_LICENSE_ATTRIBUTES,
    OVERTURE_GUIDE_FORMAT,
    PARTITION_FORMAT,
)

COLLECTION_DESCRIPTION_FORMAT = (
    "## Overture Maps - {theme}\n\n"
    "This collection contains items for the {theme} theme.\n\n"
    "{theme_description}\n\n"
    "See the official [guide]({guide_url}) for tips on querying and analyzing this "
    "dataset.\n\n"
    "## Data assets\n\n"
    "The features are provided as a set of "
    "[geoparquet](https://github.com/opengeospatial/geoparquet) datasets. The data "
    "are partitioned by\n\n"
    "1. Theme\n2. Type\n\n"
    "Each `(Theme, Type)` pair will have one or more geoparquet files, depending on "
    "the density of the of the features in that area.\n\n"
    "Note that older items in this dataset (version 2024.02.15-alpha.0 and earlier) "
    "are **not** spatially partitioned. We recommend using data with a release of  "
    "2023-03-12-alpha.0 or newer. "
    "The release is part of the URL for each parquet file and is captured in the STAC "
    "metadata for each item (see below).\n\n"
    "## STAC metadata\n\n"
    "The `overture:type` property can be used to filter items to a specific feature "
    "type, and the `version` property can be used to filter items to a "
    "specific release.\n\n"
    "## About Overture Maps\n\n"
    "Overture is a collaborative open-data initiative led by software developers, data "
    "experts,cartographic engineers, and product managers from dozens of Overture Maps "
    "Foundation member companies. Since our launch in December 2022, Overture members "
    "have been working toward a shared vision: to create reliable, user-friendly, and "
    "interoperable open map data that supports both current and future map products. "
    "We envision a world where shared, open base layers drive collaboration and "
    "innovation across industries and communities.\n\n"
    "For more information, visit the [Overture Maps Foundation](https://overturemaps.org/).\n\n"
)


class PyarrowArgs(TypedDict):
    where: str
    filesystem: Optional[Union[S3FileSystem, AzureBlobFileSystem]]


class Theme(str, Enum):
    ADDRESSES = "addresses"
    BASE = "base"
    BUILDINGS = "buildings"
    DIVISIONS = "divisions"
    PLACES = "places"
    TRANSPORTATION = "transportation"


class FeatureType(Enum):
    ADDRESS = ("address", Theme.ADDRESSES)
    BUILDING = ("building", Theme.BUILDINGS)
    BUILDING_PART = ("building_part", Theme.BUILDINGS)
    DIVISION = ("division", Theme.DIVISIONS)
    DIVISION_AREA = ("division_area", Theme.DIVISIONS)
    DIVISION_BOUNDARY = ("division_boundary", Theme.DIVISIONS)
    PLACE = ("place", Theme.PLACES)
    SEGMENT = ("segment", Theme.TRANSPORTATION)
    CONNECTOR = ("connector", Theme.TRANSPORTATION)
    BATHYMETRY = ("bathymetry", Theme.BASE)
    INFRASTRUCTURE = ("infrastructure", Theme.BASE)
    LAND = ("land", Theme.BASE)
    LAND_COVER = ("land_cover", Theme.BASE)
    LAND_USE = ("land_use", Theme.BASE)
    WATER = ("water", Theme.BASE)

    def __init__(self, type_name: str, theme: Theme):
        self.type_name = type_name
        self.theme = theme

    @classmethod
    def from_string(cls, type_name: str) -> "FeatureType":
        """Get FeatureType enum from string name"""
        for feature_type in cls:
            if feature_type.type_name == type_name:
                return feature_type
        raise ValueError(f"Unknown feature type: {type_name}")

    @classmethod
    def get_types_for_theme(cls, theme: Theme) -> list["FeatureType"]:
        """Get all feature types for a given theme"""
        return [ft for ft in cls if ft.theme == theme]


class StorageBackend(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    LOCAL = "local"


CLOUD_PROVIDERS = {
    StorageBackend.AWS: Provider(
        name="Amazon Web Services",
        roles=[ProviderRole.PRODUCER],
        url="https://aws.amazon.com",
    ),
    StorageBackend.AZURE: Provider(
        name="Microsoft",
        roles=[ProviderRole.HOST],
        url="https://microsoft.com",
    ),
}

THEME_LICENSES = {
    Theme.ADDRESSES: {
        "href": "https://docs.overturemaps.org/attribution/#addresses",
        "title": "various",
        "type": "text/html",
    },
    Theme.PLACES: {
        "href": "https://cdla.dev/permissive-2-0/",
        "title": "CDLA-Permissive-2.0",
        "type": "text/html",
    },
}


@dataclass
class CollectionInfo:
    storage_backend: StorageBackend
    theme: Theme
    latest_release: str

    @property
    def theme_description(self) -> str:
        """Scrape theme description from OvertureMaps/docs repo"""
        # Get the raw content
        raw_url = f"https://raw.githubusercontent.com/OvertureMaps/docs/refs/heads/main/docs/guides/{self.theme.value}.mdx"
        response = httpx.get(raw_url)

        response.raise_for_status()

        content = response.text

        pattern = "## Overview\n\n(.*?)(?:\n\n##|\n\n\\|)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            return match.group(1).strip()
        else:
            raise ValueError(
                f"could not retrieve content for the {self.theme.value} theme from "
                + raw_url
            )

    def to_collection(self) -> Collection:
        """Generate a pystac.Collection object for this theme/storage_backend
        combination"""
        extent = Extent(
            SpatialExtent([[-180.0, 90.0, 180.0, -90.0]]),
            TemporalExtent(
                [
                    [
                        FIRST_RELEASE_DATE,
                        datetime.strptime(self.latest_release[:10], "%Y-%M-%d"),
                    ]
                ]
            ),
        )

        providers = [
            Provider(
                name="Overture Maps Foundation",
                roles=[ProviderRole.PRODUCER],
                url="https://overturemaps.org/",
            )
        ]
        if cloud_provider := CLOUD_PROVIDERS.get(self.storage_backend):
            providers.append(cloud_provider)

        # keywords
        keywords = [
            "overture",
            "geoparquet",
        ]
        keywords.extend(
            [
                feature_type.value[0]
                for feature_type in FeatureType.get_types_for_theme(self.theme)
            ]
        )
        if self.theme != Theme.BASE:
            keywords.append(self.theme.value)

        collection = Collection(
            id=COLLECTION_ID_FORMAT.format(theme=self.theme.value),
            description=COLLECTION_DESCRIPTION_FORMAT.format(
                theme=self.theme.value,
                theme_description=self.theme_description,
                guide_url=OVERTURE_GUIDE_FORMAT.format(theme=self.theme.value),
            ),
            extent=extent,
            license=THEME_LICENSES.get(self.theme, ODBL_LICENSE_ATTRIBUTES)["title"],
            providers=providers,
            keywords=keywords,
            extra_fields={
                "overture:theme": self.theme,
            },
        )

        item_assets_ext = ItemAssetsExtension.ext(collection, add_if_missing=True)
        item_assets_ext.item_assets = {
            "data": AssetDefinition.create(
                media_type=MediaType.PARQUET,
                roles=["data"],
                title="Geoparquet partition",
                description="Geoparquet partition",
            )
        }

        # links
        collection_license = THEME_LICENSES.get(self.theme, ODBL_LICENSE_ATTRIBUTES)
        collection.add_links(
            links=[
                Link(
                    rel=RelType.LICENSE,
                    target=collection_license["href"],
                    title=collection_license["title"],
                    media_type=collection_license["type"],
                )
            ]
        )

        return collection


@dataclass
class PartitionInfo:
    href: str
    storage_backend: StorageBackend
    release: str
    theme: Theme
    feature_type: FeatureType
    part: str
    uid: str
    _datetime: datetime
    _metadata: Optional[pq.FileMetaData] = None

    @classmethod
    def from_href(cls, href: str) -> "PartitionInfo":
        """Parse PartitionInfo from a href string.

        Args:
            href: URL or file path string following a pattern:
                '{protocol}://{netloc}/release/{release}/theme={theme}/type={type}/part-{part}-{uid}.zstd.parquet'

        Returns:
            PartitionInfo object
        """
        # Parse URL to get just the path portion
        parsed_url = urlparse(href)

        protocol = parsed_url.scheme or "file"

        if protocol == "file":
            storage_backend = StorageBackend.LOCAL
        elif protocol == "s3":
            storage_backend = StorageBackend.AWS
        elif parsed_url.netloc == AZURE_NETLOC:
            storage_backend = StorageBackend.AZURE
        else:
            raise ValueError(f"could not parse storage backend from {href}")

        path = parsed_url.path

        # If there's no path component (like in s3://), use the whole href
        if not path:
            path = href

        # Find the 'release' part in the path and only parse from there
        release_idx = path.find("/release/")
        if release_idx == -1:
            raise ValueError(f"could not find /release/ in path: {path}")

        path_to_parse = path[release_idx:]
        parsed = parse(PARTITION_FORMAT, path_to_parse)

        if not isinstance(parsed, Result):
            raise ValueError(f"could not parse partition info from {href}")

        return cls(
            href=href,
            storage_backend=storage_backend,
            release=parsed["release"],
            theme=parsed["theme"],
            feature_type=parsed["type"],
            part=parsed["part"],
            uid=parsed["uid"],
            _datetime=datetime.strptime(parsed["release"][:10], "%Y-%M-%d"),
        )

    @property
    def metadata(self) -> pq.FileMetaData:
        """Parquet file metadata"""
        if self._metadata is None:
            pyarrow_args: PyarrowArgs

            if self.storage_backend == StorageBackend.AZURE:
                import adlfs

                pyarrow_args = {
                    "where": self.href.replace(f"https://{AZURE_NETLOC}/", ""),
                    "filesystem": adlfs.AzureBlobFileSystem(
                        **PYARROW_CONFIGS[self.storage_backend]
                    ),
                }
            elif self.storage_backend == StorageBackend.AWS:
                import s3fs

                pyarrow_args = {
                    "where": self.href,
                    "filesystem": s3fs.S3FileSystem(
                        **PYARROW_CONFIGS[self.storage_backend]
                    ),
                }
            else:
                pyarrow_args = {"where": self.href, "filesystem": None}

            self._metadata = pq.read_metadata(**pyarrow_args)

        return self._metadata

    @property
    def geo_metadata(self) -> Dict[str, Any]:
        geo_metadata = json.loads(self.metadata.metadata[b"geo"].decode("utf-8"))
        if not isinstance(geo_metadata, dict):
            raise ValueError(f"could not parse geo metadata from {self.href}")

        return geo_metadata

    @property
    def bbox(self) -> List[float]:
        bbox: List[float] = self.geo_metadata["columns"]["geometry"]["bbox"]
        if not all(isinstance(x, float) for x in bbox):
            raise ValueError(
                f"could not parse bounding box from {self.href}: {str(bbox)}"
            )

        return bbox

    def to_item(self) -> Item:
        collection = COLLECTION_ID_FORMAT.format(theme=self.theme)
        asset = Asset(
            href=self.href,
            roles=["data"],
            media_type=MediaType.PARQUET,
        )

        item = Item(
            id=f"{self.theme}-{self.feature_type}-{self.release}-part-{self.part}-{self.uid}",
            datetime=self._datetime,
            bbox=self.bbox,
            geometry=Polygon.from_bounds(*self.bbox).model_dump(exclude_none=True),
            properties={
                "overture:theme": self.theme,
                "overture:type": self.feature_type,
            },
            assets={"data": asset},
            collection=collection,
        )

        # version extension
        VersionExtension.ext(item, add_if_missing=True)
        item.ext.version.version = self.release

        # table extension
        table.TableExtension.ext(asset, add_if_missing=True)
        if storage_options := PYARROW_CONFIGS.get(self.storage_backend):
            asset.ext.table.storage_options = storage_options  # type: ignore

        table.TableExtension.ext(item, add_if_missing=True)
        item.ext.table.row_count = self.metadata.num_rows

        item.ext.table.columns = [
            table.Column(
                properties={
                    "name": col["name"],
                    "col_type": col["type"]
                    if isinstance(col["type"], str)
                    else col["type"].get("type"),
                }
            )
            for col in json.loads(
                self.metadata.metadata[b"org.apache.spark.sql.parquet.row.metadata"]
            )["fields"]
        ]

        # set primary geometry type to first geometry_type in geoparquet metadata
        item.ext.table.primary_geometry = self.geo_metadata["columns"]["geometry"][
            "geometry_types"
        ][0]

        item.add_link(
            Link(
                RelType.COLLECTION,
                collection,
                media_type=MediaType.JSON,
            )
        )

        return item


PYARROW_CONFIGS = {
    StorageBackend.AWS: {"anon": True},
    StorageBackend.AZURE: {"anon": True, "account_name": "overturemapswestus2"},
}
