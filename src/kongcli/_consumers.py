from datetime import datetime, timezone
import sys
from typing import Optional, Tuple

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._kong import add, all_of, consumer_acls, consumer_add_group, consumer_delete_group, delete, retrieve


@click.command()
@click.option(
    "--full-keys/--no-full-keys",
    default=False,
    help="Whether to show full keys for key-auth.",
)
@click.pass_context
def list_consumers(ctx: click.Context, full_keys: bool) -> None:
    """List all consumers along with relevant information."""
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
            "id": c['id'],
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

    apikey = ctx.obj["apikey"]
    url = ctx.obj["url"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    user = add("consumers", url, apikey, username=username, custom_id=custom_id)
    if "created_at" in user:
        user["created_at"] = datetime.fromtimestamp(
            user["created_at"] / 1000, timezone.utc
        )
    print(tabulate([user], headers="keys", tablefmt=tablefmt))


@click.command()
@click.argument("id_username")
@click.option(
    "--acls/--no-acls",
    default=False,
    help="Get all acls for the user.",
)
@click.pass_context
def retrieve_consumer(ctx: click.Context, id_username: str, acls: bool) -> None:
    """Retrieve a specific consumer."""

    apikey = ctx.obj["apikey"]
    url = ctx.obj["url"]
    tablefmt = ctx.obj["tablefmt"]

    user = retrieve("consumers", url, apikey, id_username)
    if "created_at" in user:
        user["created_at"] = datetime.fromtimestamp(
            user["created_at"] / 1000, timezone.utc
        )

    if acls:
        user['acls'] = '\n'.join(consumer_acls(url, apikey, id_username))
    print(tabulate([user], headers="keys", tablefmt=tablefmt))


@click.command()
@click.argument("id_username")
@click.argument("groups", nargs=-1)
@click.pass_context
def add_groups(ctx: click.Context, id_username: str, groups: Tuple[str, ...]) -> None:
    """Add the given groups to the consumer."""

    if not groups:
        return

    apikey = ctx.obj["apikey"]
    url = ctx.obj["url"]

    for group in groups:
        consumer_add_group(url, apikey, id_username, group)

    ctx.invoke(retrieve_consumer, id_username=id_username, acls=True)


@click.command()
@click.argument("id_username")
@click.argument("groups", nargs=-1)
@click.pass_context
def delete_groups(ctx: click.Context, id_username: str, groups: Tuple[str, ...]) -> None:
    """Delete the given groups from the consumer."""

    if not groups:
        return

    apikey = ctx.obj["apikey"]
    url = ctx.obj["url"]

    for group in groups:
        consumer_delete_group(url, apikey, id_username, group)

    ctx.invoke(retrieve_consumer, id_username=id_username, acls=True)


@click.command()
@click.argument("id_username")
@click.pass_context
def delete_consumer(ctx: click.Context, id_username: str) -> None:
    """Delete a consumer with all associated plugins / acls etc.

    Provide the unique identifier xor the name of the consumer to delete.
    """
    apikey = ctx.obj["apikey"]
    url = ctx.obj["url"]

    delete("consumers", url, apikey, id_username)
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
