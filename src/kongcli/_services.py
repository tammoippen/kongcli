from operator import itemgetter

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._kong import all_of


@click.command()
@click.pass_context
def list_services(ctx: click.Context) -> None:
    apikey = ctx.obj["apikey"]
    url = ctx.obj["url"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Service", font=font, width=160)

    services_data = all_of("services", url, apikey)
    plugins_data = all_of("plugins", url, apikey)

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
