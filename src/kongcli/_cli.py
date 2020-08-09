import sys
from typing import Any, Optional

import click
from loguru import logger
import pkg_resources
from tabulate import tabulate_formats

from ._consumers import consumers_cli, list_consumers
from ._plugins import list_global_plugins, plugins_cli
from ._raw import raw
from ._routes import list_routes, routes_cli
from ._services import list_services, services_cli
from ._session import LiveServerSession
from ._util import get, json_pretty
from .kong.general import information, status_call


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--url", envvar="KONG_BASE", help="Base url to kong.", required=True)
@click.option("--apikey", envvar="KONG_APIKEY", help="API key for key-auth to kong.")
@click.option("--basic", envvar="KONG_BASIC_USER", help="Basic auth username for kong.")
@click.option(
    "--passwd",
    envvar="KONG_BASIC_PASSWD",
    help="Basic auth password for kong. Is also prompted, if left out.",
)
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
@click.version_option(version=pkg_resources.get_distribution("kongcli").version)
@click.option("-v", "--verbose", count=True, help="Add more verbose output.")
@click.pass_context
def cli(
    ctx: click.Context,
    url: str,
    apikey: Optional[str],
    basic: Optional[str],
    passwd: Optional[str],
    tablefmt: str,
    font: str,
    verbose: int,
) -> None:
    """Interact with your kong admin api.

    Some options can also be configured via environment variables:

    \b
    --url KONG_BASE            base url to the kong admin api
    --apikey KONG_APIKEY       api key for the kong admin api
    --basic KONG_BASIC_USER    basic auth username for kong admin api
    --passwd KONG_BASIC_PASSWD basic auth password for the kong admin api
    """
    ctx.ensure_object(dict)
    logger.remove()
    if verbose == 0:
        logger.add(sys.stderr, level="ERROR")
    if verbose == 1:
        logger.add(sys.stderr, level="WARNING")
    if verbose == 2:
        logger.add(sys.stderr, level="INFO")
    if verbose >= 3:
        logger.add(sys.stderr, level="DEBUG")

    session: Optional[LiveServerSession] = ctx.obj.get("session")
    if session is None:
        # injected in the testing
        session = LiveServerSession(url)
        ctx.obj["session"] = session

    if apikey:
        session.headers.update({"apikey": apikey})
    if basic and not passwd:
        passwd = click.prompt(f"Password for `{basic}`", hide_input=True)
    if basic and passwd:
        session.auth = (basic, passwd)

    ctx.obj["tablefmt"] = tablefmt
    ctx.obj["font"] = font


@cli.resultcallback()
def cleanup(*args: Any, **kwargs: Any) -> None:
    ctx = click.get_current_context()
    ctx.obj["session"].close()


cli.add_command(consumers_cli)
cli.add_command(plugins_cli)
cli.add_command(services_cli)
cli.add_command(routes_cli)
cli.add_command(raw)


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show information on the kong instance."""
    info = get("information", lambda: information(ctx.obj["session"]))
    click.echo(json_pretty(info))


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show status information on the kong instance."""
    info = get("status", lambda: status_call(ctx.obj["session"]))
    click.echo(json_pretty(info))


@cli.group(name="list", chain=True)
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List various resources (chainable)."""
    pass


list_cmd.add_command(list_consumers, name="consumers")
list_cmd.add_command(list_global_plugins, name="global-plugins")
list_cmd.add_command(list_routes, name="routes")
list_cmd.add_command(list_services, name="services")
