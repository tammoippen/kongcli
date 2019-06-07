from functools import partial
import json

import click

click.option = partial(click.option, show_default=True)  # type: ignore # noqa: E402

from ._kong import information
from ._list import list_cmd


@click.group()
@click.option("--url", envvar="KONG_BASE", help="Base url to kong.")
@click.option("--apikey", envvar="KONG_APIKEY", help="API key for key-auth to kong.")
@click.pass_context
def cli(ctx: click.Context, url: str, apikey: str) -> None:
    """Interact with your kong admin api."""
    ctx.ensure_object(dict)
    ctx.obj["url"] = url
    ctx.obj["apikey"] = apikey


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show information on the kong instance."""
    print(json.dumps(information(ctx.obj["url"], ctx.obj["apikey"]), indent=2))


cli.add_command(list_cmd)

if __name__ == "__main__":
    cli(obj={})
