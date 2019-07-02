from operator import itemgetter

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._kong import all_of


@click.command()
@click.pass_context
def list_services(ctx: click.Context) -> None:
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Service", font=font, width=160)

    services_data = ctx.obj.get("services", all_of("services", session))
    plugins_data = ctx.obj.get("plugins", all_of("plugins", session))

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
