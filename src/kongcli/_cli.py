from functools import partial
import json

import click
from tabulate import tabulate_formats

click.option = partial(click.option, show_default=True)  # type: ignore # noqa: E402

from ._consumers import list_consumers
from ._kong import information
from ._plugins import list_global_plugins
from ._routes import list_routes
from ._services import list_services


@click.group()
@click.option("--url", envvar="KONG_BASE", help="Base url to kong.")
@click.option("--apikey", envvar="KONG_APIKEY", help="API key for key-auth to kong.")
@click.option("--tablefmt", default="fancy_grid", help=f"Format for the output tables. Supported formats: {', '.join(tabulate_formats)}")
@click.option("--font", default="banner", help="Font for the table headers. See http://www.figlet.org/examples.html for examples.")
@click.pass_context
def cli(ctx: click.Context, url: str, apikey: str, tablefmt: str, font: str) -> None:
    """Interact with your kong admin api."""
    ctx.ensure_object(dict)
    ctx.obj["url"] = url
    ctx.obj["apikey"] = apikey
    ctx.obj["tablefmt"] = tablefmt
    ctx.obj["font"] = font


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show information on the kong instance."""
    print(json.dumps(information(ctx.obj["url"], ctx.obj["apikey"]), indent=2))


@cli.group(name="list", chain=True)
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List various resources (chainable)."""
    pass


list_cmd.add_command(list_consumers, name="consumers")
list_cmd.add_command(list_global_plugins, name="global-plugins")
list_cmd.add_command(list_routes, name="routes")
list_cmd.add_command(list_services, name="services")


if __name__ == "__main__":
    cli(obj={})
