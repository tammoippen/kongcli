from functools import partial
import json
import sys

import click
from loguru import logger
from tabulate import tabulate_formats

click.option = partial(click.option, show_default=True)  # type: ignore # noqa: E402

from ._consumers import consumers, list_consumers
from ._kong import information
from ._plugins import list_global_plugins
from ._routes import list_routes
from ._services import list_services
from ._session import LiveServerSession


@click.group()
@click.option("--url", envvar="KONG_BASE", help="Base url to kong.")
@click.option("--apikey", envvar="KONG_APIKEY", help="API key for key-auth to kong.")
@click.option(
    "--tablefmt",
    default="fancy_grid",
    help=f"Format for the output tables. Supported formats: {', '.join(tabulate_formats)}",
)
@click.option(
    "--font",
    default="banner",
    help="Font for the table headers. See http://www.figlet.org/examples.html for examples.",
)
@click.option("-v", "--verbose", count=True, help="Add more verbose output.")
@click.pass_context
def cli(
    ctx: click.Context, url: str, apikey: str, tablefmt: str, font: str, verbose: int
) -> None:
    """Interact with your kong admin api."""
    ctx.ensure_object(dict)
    logger.remove()
    if verbose == 1:
        logger.add(sys.stdout, level="WARNING")
    if verbose == 2:
        logger.add(sys.stdout, level="INFO")
    if verbose == 3:
        logger.add(sys.stdout, level="DEBUG")

    session = LiveServerSession(url)
    session.headers.update({"apikey": apikey})

    ctx.obj["session"] = session
    ctx.obj["tablefmt"] = tablefmt
    ctx.obj["font"] = font


cli.add_command(consumers)


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show information on the kong instance."""
    print(json.dumps(information(ctx.obj["session"]), indent=2))


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
