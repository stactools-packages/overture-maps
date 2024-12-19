import stactools.core
from stactools.cli.registry import Registry
from stactools.overture_maps.stac import create_collection, create_item

__all__ = ["create_collection", "create_item"]

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.overture_maps import commands

    registry.register_subcommand(commands.create_overturemaps_command)
