from operator import itemgetter
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

import click
from loguru import logger
from pyfiglet import print_figlet
from tabulate import tabulate

from ._plugins import (
    enable_acl_routes,
    enable_basic_auth_routes,
    enable_key_auth_routes,
    enable_rate_limiting_routes,
    enable_request_size_limiting_routes,
    enable_response_ratelimiting_routes,
)
from ._util import get, json_pretty, parse_datetimes
from .kong import general


@click.command()
@click.option(
    "--full-plugins/--no-full-plugins",
    default=False,
    help="Whether to show full plugin config.",
)
@click.pass_context
def list_routes(ctx: click.Context, full_plugins: bool) -> None:
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
            "methods": r["methods"],
            "protocols": r["protocols"],
            "hosts": r.get("hosts"),
            "paths": r["paths"],
            "whitelist": set(),
            "blacklist": set(),
            "plugins": [],
        }
        for s in services:
            if s["id"] == r["service"]["id"]:
                rdata["service_name"] = s["name"]
                break
        for p in plugins:
            if p.get("route", {}) is None:
                # kong 1.x sets route to none, if plugin is not accoziated to a route
                continue
            if r["id"] in (p.get("route_id"), p.get("route", {}).get("id")):
                if p["name"] == "acl":
                    rdata["whitelist"] |= set(p["config"].get("whitelist", []))
                    rdata["blacklist"] |= set(p["config"].get("blacklist", []))
                elif full_plugins:
                    rdata["plugins"] += [f"{p['name']}:\n{json_pretty(p['config'])}"]
                else:
                    rdata["plugins"] += [p["name"]]
        rdata["whitelist"] = "\n".join(sorted(rdata["whitelist"]))
        rdata["blacklist"] = "\n".join(sorted(rdata["blacklist"]))
        rdata["plugins"] = "\n".join(rdata["plugins"])
        data.append(rdata)

    click.echo(
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
    click.echo(tabulate([route], headers="keys", tablefmt=tablefmt))


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
    service = general.retrieve("services", session, route["service"]["id"])
    parse_datetimes(service)

    print_figlet("Route", font=font, width=160)
    click.echo(tabulate([route], headers="keys", tablefmt=tablefmt))
    print_figlet("* Service", font=font, width=160)
    click.echo(tabulate([service], headers="keys", tablefmt=tablefmt))

    if plugins:
        plugins_entities = general.get_assoziated(
            "routes", session, route["id"], "plugins"
        )
        for p in plugins_entities:
            parse_datetimes(p)
        print_figlet("* Plugins", font=font, width=160)
        click.echo(tabulate(plugins_entities, headers="keys", tablefmt=tablefmt))


@click.command()
@click.argument("uuid_id")
@click.pass_context
def delete(ctx: click.Context, uuid_id: str) -> None:
    """Delete a route with all associated plugins.

    Provide the unique identifier of the route to delete.
    """
    session = ctx.obj["session"]

    general.delete("routes", session, uuid_id)
    click.echo(f"Deleted route `{uuid_id}`!")


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
    help="Determines the relative order of this Route against others when evaluating regex paths. Routes with higher numbers will have their regex paths evaluated first.",
)
@click.option(
    "--strip_path",
    type=bool,
    help="When matching a Route via one of the paths, strip the matching prefix from the upstream request URL.",
)
@click.option(
    "--preserve_host",
    type=bool,
    help="When matching a Route via one of the hosts domain names, use the request Host header in the upstream request headers. If set to `false`, the upstream Host header will be that of the Service’s host.",
)
@click.option(
    "--service",
    type=click.UUID,
    help="The Service this Route is associated to. This is where the Route proxies traffic to.",
)
@click.argument("uuid_id")
@click.pass_context
def update(
    ctx: click.Context,
    uuid_id: str,
    protocols: Tuple[str, ...],
    methods: Tuple[str, ...],
    hosts: Tuple[str, ...],
    paths: Tuple[str, ...],
    regex_priority: Optional[int],
    strip_path: Optional[bool],
    preserve_host: Optional[bool],
    service: Optional[UUID],
) -> None:
    """Update a route."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    payload: Dict[str, Any] = {}

    if protocols:
        payload["protocols"] = list(set(protocols))
    if methods:
        payload["methods"] = list(set(methods))
    if hosts:
        payload["hosts"] = list(set(hosts))
    if paths:
        payload["paths"] = list(set(paths))
    if regex_priority is not None:
        payload["regex_priority"] = regex_priority
    if strip_path is not None:
        payload["strip_path"] = strip_path
    if preserve_host is not None:
        payload["preserve_host"] = preserve_host
    if service is not None:
        payload["service"] = {"id": str(service)}

    if not payload:
        logger.info("Nothing to update.")
        ctx.invoke(retrieve, uuid_id=uuid_id)
        return

    route = general.update("routes", session, uuid_id, **payload)
    parse_datetimes(route)
    click.echo(tabulate([route], headers="keys", tablefmt=tablefmt))


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
routes_cli.add_command(update)
routes_cli.add_command(list_routes, name="list")
routes_cli.add_command(enable_basic_auth_routes, name="enable-basic-auth")
routes_cli.add_command(enable_key_auth_routes, name="enable-key-auth")
routes_cli.add_command(enable_acl_routes, name="enable-key-auth")
routes_cli.add_command(enable_rate_limiting_routes, name="enable-rate-limiting")
routes_cli.add_command(
    enable_request_size_limiting_routes, name="enable-request-size-limiting"
)
routes_cli.add_command(
    enable_response_ratelimiting_routes, name="enable-response-ratelimiting"
)
