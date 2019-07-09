from operator import itemgetter
from typing import Any, Dict, Tuple
from uuid import UUID

import click
from loguru import logger
from pyfiglet import print_figlet
from tabulate import tabulate

from ._util import get, parse_datetimes
from .kong import general


@click.command()
@click.pass_context
def list_routes(ctx: click.Context) -> None:
    """List all routes along with relevant information."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Routes", font=font, width=160)

    services = get("services", lambda: general.all_of("services", session))
    routes = get("routes", lambda: general.all_of("routes", session))
    plugins = get("plugins", lambda: general.all_of("plugins", session))

    data = []
    for r in routes:
        rdata = {
            "route_id": r["id"],
            "service_name": None,
            "protocols": r["protocols"],
            "hosts": r.get("hosts"),
            "paths": r["paths"],
            "whitelist": set(),
            "plugins": set(),
        }
        for s in services:
            if s["id"] == r["service"]["id"]:
                rdata["service_name"] = s["name"]
                break
        for p in plugins:
            if p.get("route_id") == r["id"]:
                if p["name"] == "acl":
                    rdata["whitelist"] |= set(p["config"]["whitelist"])
                else:
                    rdata["plugins"] |= {p["name"]}
        rdata["whitelist"] = "\n".join(rdata["whitelist"])
        rdata["plugins"] = "\n".join(rdata["plugins"])
        data.append(rdata)

    print(
        tabulate(
            sorted(data, key=itemgetter("service_name")),
            headers="keys",
            tablefmt=tablefmt,
        )
    )


@click.command()
@click.option(
    "--protocols",
    type=click.Choice(["http", "https"]),
    help='A list of the protocols this Route should allow. By default it is ["http", "https"], which means that the Route accepts both. When set to ["https"], HTTP requests are answered with a request to upgrade to HTTPS. (semi-optional)',
    multiple=True,
)
@click.option(
    "--methods",
    help='A list of HTTP methods that match this Route. For example: ["GET", "POST"]. (semi-optional)',
    multiple=True,
)
@click.option(
    "--hosts",
    help="A list of domain names that match this Route. For example: example.com. (semi-optional)",
    multiple=True,
)
@click.option(
    "--paths",
    help="A list of paths that match this Route. For example: /my-path.",
    multiple=True,
)
@click.option(
    "--regex_priority",
    type=int,
    default=0,
    help="Determines the relative order of this Route against others when evaluating regex paths. Routes with higher numbers will have their regex paths evaluated first.",
)
@click.option(
    "--strip_path",
    default=True,
    type=bool,
    help="When matching a Route via one of the paths, strip the matching prefix from the upstream request URL.",
)
@click.option(
    "--preserve_host",
    default=False,
    type=bool,
    help="When matching a Route via one of the hosts domain names, use the request Host header in the upstream request headers. If set to `false`, the upstream Host header will be that of the Service’s host.",
)
@click.option(
    "--service",
    type=click.UUID,
    help="The Service this Route is associated to. This is where the Route proxies traffic to.",
    required=True,
)
@click.pass_context
def add(
    ctx: click.Context,
    protocols: Tuple[str, ...],
    methods: Tuple[str, ...],
    hosts: Tuple[str, ...],
    paths: Tuple[str, ...],
    regex_priority: int,
    strip_path: bool,
    preserve_host: bool,
    service: UUID,
) -> None:
    """Add a route to kong.

    At least one of hosts, paths, or methods must be set.
    """
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    payload: Dict[str, Any] = {
        "regex_priority": regex_priority,
        "strip_path": strip_path,
        "preserve_host": preserve_host,
        "service": {"id": str(service)},
    }

    if not (methods or hosts or paths):
        logger.error("At least one of hosts, paths, or methods must be set.")
        raise click.Abort()

    if protocols:
        payload["protocols"] = list(set(protocols))
    if methods:
        payload["methods"] = list(set(methods))
    if hosts:
        payload["hosts"] = list(set(hosts))
    if paths:
        payload["paths"] = list(set(paths))

    route = general.add("routes", session, **payload)
    parse_datetimes(route)
    print(tabulate([route], headers="keys", tablefmt=tablefmt))


@click.command()
@click.option(
    "--plugins/--no-plugins", default=False, help="Get all plugins for the route."
)
@click.argument("uuid_id")
@click.pass_context
def retrieve(ctx: click.Context, uuid_id: str, plugins: bool) -> None:
    """Retrieve a specific route."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    route = general.retrieve("routes", session, uuid_id)
    parse_datetimes(route)
    service = general.retrieve("services", session, route['service']['id'])
    parse_datetimes(service)

    print_figlet("Route", font=font, width=160)
    print(tabulate([route], headers="keys", tablefmt=tablefmt))
    print_figlet("* Service", font=font, width=160)
    print(tabulate([service], headers="keys", tablefmt=tablefmt))

    if plugins:
        plugins_entities = general.get_assoziated(
            "routes", session, route["id"], "plugins"
        )
        for p in plugins_entities:
            parse_datetimes(p)
        print_figlet("* Plugins", font=font, width=160)
        print(tabulate(plugins_entities, headers="keys", tablefmt=tablefmt))


@click.command()
@click.argument("uuid_id")
@click.pass_context
def delete(ctx: click.Context, uuid_id: str) -> None:
    """Delete a route with all associated plugins.

    Provide the unique identifier of the route to delete.
    """
    session = ctx.obj["session"]

    general.delete("routes", session, uuid_id)
    print(f"Deleted route `{uuid_id}`!")


@click.group(name="routes")
def routes_cli() -> None:
    """Manage Routes Objects.

    The Route entities defines rules to match client requests. Each Route is
    associated with a Service, and a Service may have multiple Routes
    associated to it. Every request matching a given Route will be proxied
    to its associated Service.

    The combination of Routes and Services (and the separation of concerns
    between them) offers a powerful routing mechanism with which it is possible
    to define fine-grained entry-points in Kong leading to different upstream
    services of your infrastructure.
    """
    pass


routes_cli.add_command(add)
routes_cli.add_command(retrieve)
routes_cli.add_command(delete)
# routes_cli.add_command(update)
routes_cli.add_command(list_routes, name="list")
