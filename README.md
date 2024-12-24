# stactools-overture-maps

[![PyPI](https://img.shields.io/pypi/v/stactools-overture-maps?style=for-the-badge)](https://pypi.org/project/stactools-overture-maps/)
![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/stactools-packages/overture-maps/continuous-integration.yml?style=for-the-badge)

- Name: overture-maps
- Package: `stactools.overture_maps`
- [stactools-overture-maps on PyPI](https://pypi.org/project/stactools-overture-maps/)
- Owner: @hrodmn
- [Dataset homepage](https://docs.overturemaps.org/)
- STAC extensions used:
  - [table](https://github.com/stac-extensions/table/)
  - [version](https://github.com/stac-extensions/version/)
  - [item-assets](https://github.com/stac-extensions/item-assets/)
- Extra fields:
  - `overture:theme`: Overture Maps theme
  - `overture:type`: Overture Maps feature type
  - `overture:release`: Overture Maps release
- [Browse the example in human-readable form](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/overture-maps/main/examples/catalog.json)
- [Browse a notebook demonstrating the example item and collection](https://github.com/stactools-packages/overture-maps/tree/main/docs/example.ipynb)

This package can be used to generate STAC metadata for the Overture Maps dataset.
Collections are separated by the Overture 'Themes': Addresses, Base, Buildings, Divisions, Places, and Transportation.

Items represent individual parquet files in object storage and each one will correspond to a single partition for a theme (`overture:theme`), feature type (`overture:type:`), and release (`overture:release`).

Ideally we would include some collection-level assets for the entire `theme/type` table connections, but that will come in a later version of this package.

## STAC examples

- [Collection](examples/collection.json)
- [Item](examples/item/item.json)

## Installation

You will want to install either the `azure` or `aws` extras depending on which storage backend you intende to reference:

```shell
pip install stactools-overture-maps[azure]
```

or

```shell
pip install stactools-overture-maps[aws]
```

## Command-line usage

You can create a collection with the theme, storage backend (`azure` or `aws`), and latest release version:

```bash
stac overturemaps create-collection \
  buildings \
  azure \
  2024-12-18.0 \
  collection.json
```

You can create an item with just the `href` for the parquet asset:

```bash
stac overturemaps create-item \
  https://oveturemapswestus2.blob.core.windows.net/release/2024-12-18.0/theme=addresses/type=address/part-00000-de803747-d78d-4060-b3da-da6dcd5dbab8-c000.zstd.parquet \
  item.json
```

After generating item metadata for a new release, you should update the collection metadata to capture the new temporal extent.

Use `stac overture-maps --help` to see all subcommands and options.

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
uv sync --all-extras
uv run pre-commit install
```

To check all files:

```shell
uv run pre-commit run --all-files
```

To run the tests:

```shell
uv run pytest -vv
```

If you've updated the STAC metadata output, update the examples:

```shell
uv run scripts/update-examples
```
