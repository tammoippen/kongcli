import json
from operator import itemgetter
from typing import Dict, List

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._kong import all_of


@click.group(name="list", chain=True)
@click.option("--tablefmt", default="fancy_grid", help="Format for the output tables.")
@click.option("--font", default="banner3", help="Font for the table headers.")
@click.pass_context
def list_cmd(ctx: click.Context, tablefmt: str, font: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["tablefmt"] = tablefmt
    ctx.obj["font"] = font


@list_cmd.command()
@click.pass_context
def services(ctx: click.Context) -> None:
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


@list_cmd.command()
@click.pass_context
def routes(ctx: click.Context) -> None:
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


@list_cmd.command()
@click.option(
    "--full-keys/--no-full-keys",
    default=False,
    help="Whether to show full keys for key-auth.",
)
@click.pass_context
def consumers(ctx: click.Context, full_keys: bool) -> None:
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

    data: List[Dict[str, str]] = []
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


@list_cmd.command()
@click.pass_context
def global_plugins(ctx: click.Context) -> None:
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
