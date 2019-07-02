from datetime import datetime, timezone
import json
import sys
from typing import Optional, Tuple

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._kong import (
    add,
    all_of,
    consumer_groups,
    consumer_add_group,
    consumer_basic_auths,
    consumer_delete_group,
    consumer_key_auths,
    consumer_plugins,
    delete,
    retrieve,
)


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

    consumers = ctx.obj.get("consumers", all_of("consumers", session))
    plugins = ctx.obj.get("plugins", all_of("plugins", session))
    acls = ctx.obj.get("acls", all_of("acls", session))
    basic_auths = ctx.obj.get("basic-auth", all_of("basic-auths", session))
    key_auths = ctx.obj.get("key-auth", all_of("key-auths", session))

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


@click.command()
@click.option("--username", "-u", help="The unique username of the consumer.")
@click.option(
    "--custom_id",
    "-c",
    help="Field for storing an existing unique ID for the consumer - useful for mapping Kong with users in your existing database.",
)
@click.pass_context
def create_consumer(
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

    user = add("consumers", session, username=username, custom_id=custom_id)
    if "created_at" in user:
        user["created_at"] = datetime.fromtimestamp(
            user["created_at"] / 1000, timezone.utc
        )
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
def retrieve_consumer(
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

    user = retrieve("consumers", session, id_username)
    if "created_at" in user:
        user["created_at"] = datetime.fromtimestamp(
            user["created_at"] / 1000, timezone.utc
        )

    if acls:
        user["acls"] = "\n".join(consumer_groups(session, id_username))
    if basic_auths:
        user["basic_auth"] = "\n".join(
            f'{ba["id"]}: {ba["username"]}:xxx'
            for ba in consumer_basic_auths(session, id_username)
        )
    if key_auths:
        user["key_auth"] = "\n".join(
            f'{ba["id"]}: {ba["username"]}:xxx'
            for ba in consumer_key_auths(session, id_username)
        )
    if plugins:
        user["plugins"] = "\n\n".join(
            f"{json.dumps(plugin, indent=2)}"
            for plugin in consumer_plugins(session, id_username)
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
        consumer_add_group(session, id_username, group)

    ctx.invoke(retrieve_consumer, id_username=id_username, acls=True)


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
        consumer_delete_group(session, id_username, group)

    ctx.invoke(retrieve_consumer, id_username=id_username, acls=True)


@click.command()
@click.argument("id_username")
@click.pass_context
def delete_consumer(ctx: click.Context, id_username: str) -> None:
    """Delete a consumer with all associated plugins / acls etc.

    Provide the unique identifier xor the name of the consumer to delete.
    """
    session = ctx.obj["session"]

    delete("consumers", session, id_username)
    print(f"Deleted `{id_username}`!")


@click.group()
def consumers() -> None:
    """Manage consumers of kong.

    The Consumer object represents a consumer - or a user - of a Service. You can either
    rely on Kong as the primary datastore, or you can map the consumer list with your
    database to keep consistency between Kong and your existing primary datastore.
    """
    pass


consumers.add_command(list_consumers, name="list")
consumers.add_command(create_consumer, name="create")
consumers.add_command(retrieve_consumer, name="retrieve")
consumers.add_command(delete_consumer, name="delete")
consumers.add_command(add_groups, name="add-groups")
consumers.add_command(delete_groups, name="delete-groups")
