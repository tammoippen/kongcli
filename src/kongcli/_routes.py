from operator import itemgetter

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._util import get
from .kong import general


@click.command()
@click.pass_context
def list_routes(ctx: click.Context) -> None:
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


# routes_cli.add_command(add)
# routes_cli.add_command(retrieve)
# routes_cli.add_command(delete)
# routes_cli.add_command(update)
routes_cli.add_command(list_routes, name="list")
