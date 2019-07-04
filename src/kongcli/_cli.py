from functools import partial
import json
import sys
from typing import Optional, Tuple

import click
from loguru import logger
from tabulate import tabulate_formats

click.option = partial(click.option, show_default=True)  # type: ignore # noqa: E402

from ._consumers import consumers_cli, list_consumers
from ._plugins import list_global_plugins, plugins_cli
from ._routes import list_routes
from ._services import list_services, services_cli
from ._session import LiveServerSession
from ._util import dict_from_dot, get
from .kong.general import information


@click.group()
@click.option("--url", envvar="KONG_BASE", help="Base url to kong.", required=True)
@click.option("--apikey", envvar="KONG_APIKEY", help="API key for key-auth to kong.")
@click.option("--basic", envvar="KONG_BASIC_USER", help="Basic auth username for kong.")
@click.option(
    "--passwd",
    envvar="KONG_BASIC_PASSWD",
    help="Basic auth password for kong. Is also prompted.",
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
    """Interact with your kong admin api."""
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

    session = LiveServerSession(url)
    if apikey:
        session.headers.update({"apikey": apikey})
    if basic and not passwd:
        passwd = click.prompt(f"Password for `{basic}`", hide_input=True)
    if basic and passwd:
        session.auth = (basic, passwd)

    ctx.obj["session"] = session
    ctx.obj["tablefmt"] = tablefmt
    ctx.obj["font"] = font


cli.add_command(consumers_cli)
cli.add_command(plugins_cli)
cli.add_command(services_cli)


@cli.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show information on the kong instance."""
    info = get("information", lambda: information(ctx.obj["session"]))
    print(json.dumps(info, indent=2))


@cli.command()
@click.option("--header", "-H", type=(str, str), multiple=True, help="Add headers.")
@click.option(
    "--data",
    "-d",
    type=(str, str),
    multiple=True,
    help="Add key-value data points to the payload.",
)
@click.argument("method")
@click.argument("url")
@click.pass_context
def raw(
    ctx: click.Context,
    method: str,
    url: str,
    header: Tuple[Tuple[str, str], ...],
    data: Tuple[Tuple[str, str], ...],
) -> None:
    """Perform raw http requests to kong.

    You can provide headers using the --header / -H option:

    - to get the header 'Accept: application/json' use

        -H Accept application/json

    - to get the header 'Content-Type: application/json; charset=utf-8' use

        -H Content-Type "application/json; charset=utf-8"

    You can provide a json body using the --data / -d option

      -d foo bar          # => {"foo": "bar"}

      -d foo true         # => {"foo": true}

      -d foo '"true"'     # => {"foo": "true"}

      -d foo.bar.baz 2.3  # => {"foo": {"bar": {"baz": 2.3}}}

      -d name bar -d config.methods '["GET", "POST"]'

      # => {"name": "bar", "config": {"methods": ["GET", "POST"]}}

    If first argument to `--data / -d` is the key. It is split by dots
    and sub-dictionaries are created. The second argument is assumed to be
    valid JSON; if it cannot be parsed, we assume it is a string. Multiple
    usages of `--data / -d` will merge the dictionary.
    """
    session: LiveServerSession = ctx.obj["session"]
    headers_dict = {h[0]: h[1] for h in header}
    print(f"> {method} {session.prefix_url}{url}", file=sys.stderr)
    for k, v in session.headers.items():
        print("> ", k, ": ", v, sep="", file=sys.stderr)
    for k, v in headers_dict.items():
        print("> ", k, ": ", v, sep="", file=sys.stderr)
    print(">", file=sys.stderr)

    payload = None
    if data:
        payload = dict_from_dot(data)
    if payload:
        print("> Body:")
        print(">", json.dumps(payload))

    resp = session.request(method, url, headers=headers_dict, json=payload)
    print(f"< http/{resp.raw.version}", resp.status_code, resp.reason, file=sys.stderr)
    for k, v in resp.headers.items():
        print("< ", k, ": ", v, sep="", file=sys.stderr)
    print(file=sys.stderr)
    print(resp.text)


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
