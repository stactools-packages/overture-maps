from pystac import (
    Collection,
    Item,
)

from stactools.overture_maps.metadata import (
    CollectionInfo,
    PartitionInfo,
    StorageBackend,
    Theme,
)


def create_collection(
    theme: Theme, storage_backend: StorageBackend, latest_release: str
) -> Collection:
    """Creates a STAC Collection.

    This function should create a collection for this dataset. See `the STAC
    specification
    <https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md>`_
    for information about collection fields, and
    `Collection<https://pystac.readthedocs.io/en/latest/api.html#collection>`_
    for information about the PySTAC class.

    Returns:
        Collection: STAC Collection object
    """
    if not storage_backend:
        raise ValueError(
            f"no configuration for this cloud provider: {storage_backend.value}"
        )
    collection_config = CollectionInfo(
        storage_backend=storage_backend,
        theme=theme,
        latest_release=latest_release,
    )
    collection = collection_config.to_collection()

    return collection


def create_item(asset_href: str) -> Item:
    """Creates a STAC item from a raster asset.

    This example function uses :py:func:`stactools.core.utils.create_item` to
    generate an example item.  Datasets should customize the item with
    dataset-specific information, e.g.  extracted from metadata files.

    See `the STAC specification
    <https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md>`_
    for information about an item's fields, and
    `Item<https://pystac.readthedocs.io/en/latest/api/pystac.html#pystac.Item>`_ for
    information on the PySTAC class.

    This function should be updated to take all hrefs needed to build the item.
    It is an anti-pattern to assume that related files (e.g. metadata) are in
    the same directory as the primary file.

    Args:
        asset_href (str): The HREF pointing to an asset associated with the item

    Returns:
        Item: STAC Item object
    """
    partition_info = PartitionInfo.from_href(asset_href)

    item = partition_info.to_item()

    return item
