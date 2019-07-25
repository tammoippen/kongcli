import json
import sys
from typing import Optional, Tuple

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._util import get, parse_datetimes
from .kong import consumers, general


@click.command()
@click.option(
    "--full-keys/--no-full-keys",
    default=False,
    help="Whether to show full keys for key-auth.",
)
@click.pass_context
def list_consumers(ctx: click.Context, full_keys: bool) -> None:
    """List all consumers along with relevant information."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Consumers", font=font, width=160)

    consumers = get("consumers", lambda: general.all_of("consumers", session))
    plugins = get("plugins", lambda: general.all_of("plugins", session))
    acls = get("acls", lambda: general.all_of("acls", session))
    basic_auths = get("basic-auth", lambda: general.all_of("basic-auths", session))
    key_auths = get("key-auth", lambda: general.all_of("key-auths", session))

    data = []
    for c in consumers:
        cdata = {
            "id": c["id"],
            "custom_id": c.get("custom_id", ""),
            "username": c.get("username", ""),
            "acl_groups": set(),
            "plugins": set(),
            "basic_auth": set(),
            "key_auth": set(),
        }
        for a in acls:
            if c["id"] in (a.get("consumer_id"), a.get("consumer", {}).get("id")):
                cdata["acl_groups"] |= {a["group"]}
        for p in plugins:
            if p.get("consumer", {}) is None:
                # version 1. sets `consumer` to none, if not assigned to a consumer
                continue
            if c["id"] in (p.get("consumer_id"), p.get("consumer", {}).get("id")):
                cdata["plugins"] |= {p["name"]}
        for b in basic_auths:
            if c["id"] in (b.get("consumer_id"), b.get("consumer", {}).get("id")):
                cdata["basic_auth"] |= {f'{b["username"]}:xxx'}
        for k in key_auths:
            if c["id"] in (k.get("consumer_id"), k.get("consumer", {}).get("id")):
                key = k["key"]
                if not full_keys:
                    key = f"{key[:6]}..."
                cdata["key_auth"] |= {key}

        cdata["acl_groups"] = "\n".join(sorted(cdata["acl_groups"]))
        cdata["plugins"] = "\n".join(sorted(cdata["plugins"]))
        cdata["basic_auth"] = "\n".join(sorted(cdata["basic_auth"]))
        cdata["key_auth"] = "\n".join(sorted(cdata["key_auth"]))
        data.append(cdata)

    data.sort(key=lambda d: d["username"])
    print(tabulate(data, headers="keys", tablefmt=tablefmt))


@click.command()
@click.option("--username", help="The unique username of the consumer.")
@click.option(
    "--custom_id",
    help="Field for storing an existing unique ID for the consumer - useful for mapping Kong with users in your existing database.",
)
@click.pass_context
def create(
    ctx: click.Context, username: Optional[str], custom_id: Optional[str]
) -> None:
    """Create a user / consumer of your services / routes.

    You must select either `custom_id` or `username` or both.
    """
    if not (username or custom_id):
        print(
            "You must set either `--username` or `--custom_id` with the request.",
            file=sys.stderr,
        )
        raise click.Abort()

    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    user = general.add("consumers", session, username=username, custom_id=custom_id)
    parse_datetimes(user)
    print(tabulate([user], headers="keys", tablefmt=tablefmt))


@click.command()
@click.argument("id_username")
@click.option("--acls/--no-acls", default=False, help="Get all acls for the user.")
@click.option(
    "--basic-auths/--no-basic-auths",
    default=False,
    help="Get all basic-auth for the user.",
)
@click.option(
    "--key-auths/--no-key-auths", default=False, help="Get all key-auth for the user."
)
@click.option(
    "--plugins/--no-plugins", default=False, help="Get all plugins for the user."
)
@click.pass_context
def retrieve(
    ctx: click.Context,
    id_username: str,
    acls: bool,
    basic_auths: bool,
    key_auths: bool,
    plugins: bool,
) -> None:
    """Retrieve a specific consumer."""

    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    user = general.retrieve("consumers", session, id_username)
    parse_datetimes(user)

    if acls:
        user["acls"] = "\n".join(consumers.groups(session, id_username))
    if basic_auths:
        user["basic_auth"] = "\n".join(
            f'{ba["id"]}: {ba["username"]}:xxx'
            for ba in consumers.basic_auths(session, id_username)
        )
    if key_auths:
        user["key_auth"] = "\n".join(
            f'{ba["id"]}: {ba["username"]}:xxx'
            for ba in consumers.key_auths(session, id_username)
        )
    if plugins:
        user["plugins"] = "\n\n".join(
            f"{json.dumps(plugin, indent=2)}"
            for plugin in consumers.plugins(session, id_username)
        )
    print(tabulate([user], headers="keys", tablefmt=tablefmt))


@click.command()
@click.argument("id_username")
@click.argument("groups", nargs=-1)
@click.pass_context
def add_groups(ctx: click.Context, id_username: str, groups: Tuple[str, ...]) -> None:
    """Add the given groups to the consumer."""

    if not groups:
        return

    session = ctx.obj["session"]

    for group in groups:
        consumers.add_group(session, id_username, group)

    ctx.invoke(retrieve, id_username=id_username, acls=True)


@click.command()
@click.argument("id_username")
@click.argument("groups", nargs=-1)
@click.pass_context
def delete_groups(
    ctx: click.Context, id_username: str, groups: Tuple[str, ...]
) -> None:
    """Delete the given groups from the consumer."""

    if not groups:
        return

    session = ctx.obj["session"]

    for group in groups:
        consumers.delete_group(session, id_username, group)

    ctx.invoke(retrieve, id_username=id_username, acls=True)


@click.command()
@click.argument("id_username")
@click.pass_context
def delete(ctx: click.Context, id_username: str) -> None:
    """Delete a consumer with all associated plugins / acls etc.

    Provide the unique identifier xor the name of the consumer to delete.
    """
    session = ctx.obj["session"]

    general.delete("consumers", session, id_username)
    print(f"Deleted consumer `{id_username}`!")


@click.command()
@click.option(
    "--username",
    help="The unique username of the consumer. You must proviod either this field or custom_id.",
)
@click.option(
    "--custom_id",
    help="The unique custom_id of the consaumer. You must proviod either this field or username.",
)
@click.argument("id_username")
@click.pass_context
def update(
    ctx: click.Context,
    id_username: str,
    username: Optional[str],
    custom_id: Optional[str],
) -> None:
    """Update a consumer.

    Provide the unique identifier xor the name of the consumer to update as argument.
    """
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    payload = {}
    if username:
        payload["username"] = username
    if custom_id:
        payload["custom_id"] = custom_id

    assert payload, "At least one of `--username` or `--custom_id` has to be set."

    user = general.update("consumers", session, id_username, **payload)
    print(tabulate([user], headers="keys", tablefmt=tablefmt))


@click.group(name="consumers")
def consumers_cli() -> None:
    """Manage Consumers Objects.

    The Consumer object represents a consumer - or a user - of a Service. You can either
    rely on Kong as the primary datastore, or you can map the consumer list with your
    database to keep consistency between Kong and your existing primary datastore.
    """
    pass


consumers_cli.add_command(list_consumers, name="list")
consumers_cli.add_command(create)
consumers_cli.add_command(retrieve)
consumers_cli.add_command(delete)
consumers_cli.add_command(add_groups, name="add-groups")
consumers_cli.add_command(delete_groups, name="delete-groups")
consumers_cli.add_command(update)
