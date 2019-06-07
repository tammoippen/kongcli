import json
from operator import itemgetter

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._kong import all_of


@click.command()
@click.pass_context
def list_global_plugins(ctx: click.Context) -> None:
    apikey = ctx.obj["apikey"]
    url = ctx.obj["url"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Global Plugins", font=font, width=160)

    plugins = all_of("plugins", url, apikey)

    data = []
    for p in plugins:
        if (
            p.get("route_id") is None
            and p.get("service_id") is None
            and p.get("consumer_id") is None
        ):
            data.append(
                {"name": p["name"], "config": json.dumps(p["config"], indent=2)}
            )

    print(
        tabulate(
            sorted(data, key=itemgetter("name")), headers="keys", tablefmt=tablefmt
        )
    )
