from operator import itemgetter
from typing import Optional

import click
from loguru import logger
from pyfiglet import print_figlet
from tabulate import tabulate

from ._util import get
from .kong import general


@click.command()
@click.pass_context
def list_services(ctx: click.Context) -> None:
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Service", font=font, width=160)

    services_data = get("services", lambda: general.all_of("services", session))
    plugins_data = get("plugins", lambda: general.all_of("plugins", session))

    data = []
    for s in services_data:
        sdata = {
            "service_id": s["id"],
            "name": s["name"],
            "protocol": s["protocol"],
            "host": s["host"],
            "port": s["port"],
            "path": s["path"],
            "whitelist": set(),
            "plugins": set(),
        }
        for p in plugins_data:
            if p.get("service_id") == s["id"]:
                if p["name"] == "acl":
                    sdata["whitelist"] |= set(p["config"]["whitelist"])
                else:
                    sdata["plugins"] |= {p["name"]}
        sdata["whitelist"] = "\n".join(sdata["whitelist"])
        sdata["plugins"] = "\n".join(sdata["plugins"])
        data.append(sdata)

    print(
        tabulate(
            sorted(data, key=itemgetter("name")), headers="keys", tablefmt=tablefmt
        )
    )


@click.command()
@click.option("--name", help="The Service name.")
@click.option(
    "--protocol",
    type=click.Choice(["http", "https"]),
    help="The protocol used to communicate with the upstream. It can be one of `http` (default) or `https`.",
)
@click.option("--host", help="The host of the upstream server.")
@click.option("--port", type=int, help="The upstream server port. Defaults to 80.")
@click.option(
    "--path",
    help="The path to be used in requests to the upstream server. Defaults to ``.",
)
@click.option(
    "--retries",
    default=5,
    type=int,
    help="The number of retries to execute upon failure to proxy.",
)
@click.option(
    "--connect_timeout",
    default=60000,
    type=int,
    help="The timeout in milliseconds for establishing a connection to the upstream server.",
)
@click.option(
    "--write_timeout",
    default=60000,
    type=int,
    help="The timeout in milliseconds between two successive write operations for transmitting a request to the upstream server.",
)
@click.option(
    "--read_timeout",
    default=60000,
    type=int,
    help="The timeout in milliseconds between two successive read operations for transmitting a request to the upstream server.",
)
@click.option(
    "--url",
    help="Shorthand attribute to set protocol, host, port and path at once. This attribute is write-only (the Admin API never “returns” the url).",
)
@click.pass_context
def add(
    ctx: click.Context,
    name: Optional[str],
    protocol: Optional[str],
    host: Optional[str],
    port: Optional[int],
    path: Optional[str],
    retries: int,
    connect_timeout: int,
    write_timeout: int,
    read_timeout: int,
    url: Optional[str],
) -> None:
    """Add a service to kong."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    payload = {
        "retries": retries,
        "connect_timeout": connect_timeout,
        "write_timeout": write_timeout,
        "read_timeout": read_timeout,
    }
    if name:
        payload["name"] = name

    if url and (protocol or host or port or path):
        logger.error(
            "If using the shorthand-attribute `url` the other options `protocol`, `host`, `port` and `path` will be ignored."
        )
        raise click.Abort()

    if not url and not host:
        logger.error("If not using the shorthand-attribute `url`, at least `host` has to be set.")
        raise click.Abort()

    if url:
        payload["url"] = url
    if protocol:
        payload["protocol"] = protocol
    if host:
        payload["host"] = host
    if port:
        payload["port"] = port
    if path:
        payload["path"] = path

    serv = general.add("services", session, **payload)
    print(tabulate([serv], headers="keys", tablefmt=tablefmt))


@click.group(name="services")
def services_cli() -> None:
    pass


services_cli.add_command(add)
services_cli.add_command(list_services, name="list")
