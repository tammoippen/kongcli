# from typing import Dict, List

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._kong import all_of


@click.command()
@click.option(
    "--full-keys/--no-full-keys",
    default=False,
    help="Whether to show full keys for key-auth.",
)
@click.pass_context
def list_consumers(ctx: click.Context, full_keys: bool) -> None:
    apikey = ctx.obj["apikey"]
    url = ctx.obj["url"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Consumers", font=font, width=160)

    consumers = all_of("consumers", url, apikey)
    plugins = all_of("plugins", url, apikey)
    acls = all_of("acls", url, apikey)
    basic_auths = all_of("basic-auths", url, apikey)
    key_auths = all_of("key-auths", url, apikey)

    data = []
    for c in consumers:
        cdata = {
            "custom_id": c["custom_id"],
            "username": c["username"],
            "acl_groups": set(),
            "plugins": set(),
            "basic_auth": set(),
            "key_auth": set(),
        }
        for a in acls:
            if c["id"] == a["consumer_id"]:
                cdata["acl_groups"] |= {a["group"]}
        for p in plugins:
            if c["id"] == p.get("consumer_id"):
                cdata["plugins"] |= {p["name"]}
        for b in basic_auths:
            if c["id"] == b.get("consumer_id"):
                cdata["basic_auth"] |= {f'{b["username"]}:xxx'}
        for k in key_auths:
            if c["id"] == k.get("consumer_id"):
                key = k["key"]
                if not full_keys:
                    key = f"{key[:6]}..."
                cdata["key_auth"] |= {key}

        cdata["acl_groups"] = "\n".join(sorted(cdata["acl_groups"]))
        cdata["plugins"] = "\n".join(sorted(cdata["plugins"]))
        cdata["basic_auth"] = "\n".join(sorted(cdata["basic_auth"]))
        cdata["key_auth"] = "\n".join(sorted(cdata["key_auth"]))
        data.append(cdata)

    data.sort(key=lambda d: (len(d["custom_id"]), d["username"]))
    print(tabulate(data, headers="keys", tablefmt=tablefmt))
