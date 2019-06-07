from operator import itemgetter

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._kong import all_of


@click.command()
@click.pass_context
def list_routes(ctx: click.Context) -> None:
    apikey = ctx.obj["apikey"]
    url = ctx.obj["url"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Routes", font=font, width=160)

    services = all_of("services", url, apikey)
    routes = all_of("routes", url, apikey)
    plugins = all_of("plugins", url, apikey)

    data = []
    for r in routes:
        rdata = {
            "route_id": r["id"],
            "service_name": None,
            "protocols": r["protocols"],
            "host": r["hosts"] if r.get("host") else "api.fedger.co",
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
