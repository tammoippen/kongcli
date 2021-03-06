from operator import itemgetter
from typing import Any, Dict, Optional, Union

import click
from loguru import logger
from pyfiglet import print_figlet
from tabulate import tabulate

from ._plugins import (
    enable_acl_services,
    enable_basic_auth_services,
    enable_key_auth_services,
    enable_rate_limiting_services,
    enable_request_size_limiting_services,
    enable_response_ratelimiting_services,
)
from ._util import get, json_pretty, parse_datetimes, sort_dict, substitude_ids
from .kong import general


def sort_service_dict(obj: Any) -> Dict[str, Any]:
    service = sort_dict(obj)
    result = {}
    for k in [
        "id",
        "name",
        "tags",
        "created_at",
        "updated_at",
        "protocol",
        "host",
        "port",
        "path",
        "retries",
        "connect_timeout",
        "read_timeout",
        "write_timeout",
    ]:
        if k in service:
            result[k] = service.pop(k)

    assert service == {}
    return result


@click.command()
@click.option(
    "--full-plugins",
    is_flag=True,
    help="Whether to show full plugin config.",
)
@click.pass_context
def list_services(ctx: click.Context, full_plugins: bool) -> None:
    """List all services along with relevant information."""
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
            "blacklist": set(),
            "plugins": [],
        }
        for p in plugins_data:
            substitude_ids(p)
            if s["id"] == p.get("service.id"):
                if p["name"] == "acl":
                    sdata["whitelist"] |= set(p["config"].get("whitelist") or []) | set(
                        p["config"].get("allow") or []
                    )
                    sdata["blacklist"] |= set(p["config"].get("blacklist") or []) | set(
                        p["config"].get("deny") or []
                    )
                elif full_plugins:
                    sdata["plugins"] += [f"{p['name']}:\n{json_pretty(p['config'])}"]
                else:
                    sdata["plugins"] += [p["name"]]
        sdata["whitelist"] = "\n".join(sorted(sdata["whitelist"]))
        sdata["blacklist"] = "\n".join(sorted(sdata["blacklist"]))
        sdata["plugins"] = "\n".join(sdata["plugins"])
        data.append(sdata)

    click.echo(
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
    payload: Dict[str, Union[str, int]] = {
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
        logger.error(
            "If not using the shorthand-attribute `url`, at least `host` has to be set."
        )
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

    service = general.add("services", session, **payload)
    parse_datetimes(service)
    service = sort_service_dict(service)

    click.echo(tabulate([service], headers="keys", tablefmt=tablefmt))


@click.command()
@click.option("--plugins", is_flag=True, help="Get all plugins for the service.")
@click.option("--routes", is_flag=True, help="Get all routes for the service.")
@click.argument("id_name")
@click.pass_context
def retrieve(ctx: click.Context, id_name: str, plugins: bool, routes: bool) -> None:
    """Retrieve a specific service."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    service = general.retrieve("services", session, id_name)
    parse_datetimes(service)

    print_figlet("Service", font=font, width=160)
    click.echo(tabulate([service], headers="keys", tablefmt=tablefmt))

    if plugins:
        plugins_entities = general.get_assoziated(
            "services", session, service["id"], "plugins"
        )
        for p in plugins_entities:
            parse_datetimes(p)
        print_figlet("* Plugins", font=font, width=160)
        click.echo(tabulate(plugins_entities, headers="keys", tablefmt=tablefmt))
    if routes:
        routes_entities = general.get_assoziated(
            "services", session, service["id"], "routes"
        )
        for r in routes_entities:
            parse_datetimes(r)
        print_figlet("* Routes", font=font, width=160)
        click.echo(tabulate(routes_entities, headers="keys", tablefmt=tablefmt))


@click.command()
@click.argument("id_name")
@click.pass_context
def delete(ctx: click.Context, id_name: str) -> None:
    """Delete a service with all associated plugins / routes etc.

    Provide the unique identifier xor the name of the service to delete.
    """
    session = ctx.obj["session"]

    general.delete("services", session, id_name)
    click.echo(f"Deleted service `{id_name}`!")


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
    type=int,
    help="The number of retries to execute upon failure to proxy.",
)
@click.option(
    "--connect_timeout",
    type=int,
    help="The timeout in milliseconds for establishing a connection to the upstream server.",
)
@click.option(
    "--write_timeout",
    type=int,
    help="The timeout in milliseconds between two successive write operations for transmitting a request to the upstream server.",
)
@click.option(
    "--read_timeout",
    type=int,
    help="The timeout in milliseconds between two successive read operations for transmitting a request to the upstream server.",
)
@click.option(
    "--url",
    help="Shorthand attribute to set protocol, host, port and path at once. This attribute is write-only (the Admin API never “returns” the url).",
)
@click.argument("id_name")
@click.pass_context
def update(
    ctx: click.Context,
    id_name: str,
    name: Optional[str],
    protocol: Optional[str],
    host: Optional[str],
    port: Optional[int],
    path: Optional[str],
    retries: Optional[int],
    connect_timeout: Optional[int],
    write_timeout: Optional[int],
    read_timeout: Optional[int],
    url: Optional[str],
) -> None:
    """Update a service.

    Provide the unique identifier xor the name of the service to update as argument.
    """
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    if url and (protocol or host or port or path):
        logger.error(
            "If using the shorthand-attribute `url` the other options `protocol`, `host`, `port` and `path` will be ignored."
        )
        raise click.Abort()

    payload: Dict[str, Union[str, int]] = {}
    if name is not None:
        payload["name"] = name
    if protocol is not None:
        payload["protocol"] = protocol
    if host is not None:
        payload["host"] = host
    if port is not None:
        payload["port"] = port
    if path is not None:
        payload["path"] = path
    if retries is not None:
        payload["retries"] = retries
    if connect_timeout is not None:
        payload["connect_timeout"] = connect_timeout
    if write_timeout is not None:
        payload["write_timeout"] = write_timeout
    if read_timeout is not None:
        payload["read_timeout"] = read_timeout
    if url is not None:
        payload["url"] = url

    if not payload:
        logger.info("Nothing to update.")
        ctx.invoke(retrieve, id_name=id_name)
        return

    service = general.update("services", session, id_name, **payload)
    parse_datetimes(service)
    click.echo(tabulate([service], headers="keys", tablefmt=tablefmt))


@click.group(name="services")
def services_cli() -> None:
    """Manage Service Objects.

    Service entities, as the name implies, are abstractions of each of
    your own upstream services. Examples of Services would be a data
    transformation microservice, a billing API, etc.

    The main attribute of a Service is its URL (where Kong should proxy
    traffic to), which can be set as a single string or by specifying
    its protocol, host, port and path individually.

    Services are associated to Routes (a Service can have many Routes
    associated with it). Routes are entry-points in Kong and define
    rules to match client requests. Once a Route is matched, Kong
    proxies the request to its associated Service. See the Proxy
    Reference for a detailed explanation of how Kong proxies traffic.
    """
    pass


services_cli.add_command(add)
services_cli.add_command(retrieve)
services_cli.add_command(delete)
services_cli.add_command(update)
services_cli.add_command(enable_basic_auth_services, name="enable-basic-auth")
services_cli.add_command(enable_key_auth_services, name="enable-key-auth")
services_cli.add_command(enable_acl_services, name="enable-acl")
services_cli.add_command(enable_rate_limiting_services, name="enable-rate-limiting")
services_cli.add_command(
    enable_request_size_limiting_services, name="enable-request-size-limiting"
)
services_cli.add_command(
    enable_response_ratelimiting_services, name="enable-response-ratelimiting"
)
services_cli.add_command(list_services, name="list")
