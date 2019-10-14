import json
from typing import Optional, Tuple
from uuid import UUID

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._util import get, parse_datetimes, sort_dict
from .kong import consumers, general


@click.command()
@click.option(
    "--full-keys",
    default=False,
    is_flag=True,
    help="Whether to show full keys for key-auth.",
)
@click.option(
    "--full-plugins",
    default=False,
    is_flag=True,
    help="Whether to show full plugin config.",
)
@click.pass_context
def list_consumers(ctx: click.Context, full_keys: bool, full_plugins: bool) -> None:
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
            "plugins": [],
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
                if full_plugins:
                    cdata["plugins"] += [(p["name"], p["config"])]
                else:
                    cdata["plugins"] += [p["name"]]
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
        if full_plugins:
            cdata["plugins"] = "\n".join(
                f"{name}:\n{json.dumps(p, indent=2, sort_keys=True)}"
                for name, p in sorted(cdata["plugins"])
            )
        else:
            cdata["plugins"] = "\n".join(sorted(cdata["plugins"]))
        cdata["basic_auth"] = "\n".join(sorted(cdata["basic_auth"]))
        cdata["key_auth"] = "\n".join(sorted(cdata["key_auth"]))
        data.append(cdata)

    data.sort(key=lambda d: (len(d["custom_id"]), d["username"]))
    click.echo(tabulate(data, headers="keys", tablefmt=tablefmt))


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
        click.echo(
            "You must set either `--username` or `--custom_id` with the request.",
            err=True,
        )
        raise click.Abort()

    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    user = general.add("consumers", session, username=username, custom_id=custom_id)
    user = sort_dict(user)
    parse_datetimes(user)
    click.echo(tabulate([user], headers="keys", tablefmt=tablefmt))


@click.command()
@click.argument("id_username")
@click.option("--acls", default=False, is_flag=True, help="Get all acls for the user.")
@click.option(
    "--basic-auths",
    default=False,
    is_flag=True,
    help="Get all basic-auth for the user.",
)
@click.option(
    "--key-auths", default=False, is_flag=True, help="Get all key-auth for the user."
)
@click.option(
    "--plugins", default=False, is_flag=True, help="Get all plugins for the user."
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
    sort_dict(user)
    parse_datetimes(user)

    if acls:
        user["acls"] = "\n".join(sorted(consumers.groups(session, id_username)))
    if basic_auths:
        user["basic_auth"] = "\n".join(
            f'{ba["id"]}: {ba["username"]}:xxx'
            for ba in consumers.basic_auths(session, id_username)
        )
    if key_auths:
        user["key_auth"] = "\n".join(
            f"{ka['id']}: {ka['key']}"
            for ka in consumers.key_auths(session, id_username)
        )
    if plugins:
        user["plugins"] = "\n\n".join(
            f"{json.dumps(plugin, indent=2)}"
            for plugin in consumers.plugins(session, id_username)
        )
    click.echo(tabulate([user], headers="keys", tablefmt=tablefmt))


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
    click.echo(f"Deleted consumer `{id_username}`!")


@click.command()
@click.option(
    "--username",
    help="The unique username of the consumer. You must provide either this field or custom_id.",
)
@click.option(
    "--custom_id",
    help="The unique custom_id of the consumer. You must provide either this field or username.",
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

    if not payload:
        click.echo(
            "You must set either `--username` or `--custom_id` with the request.",
            err=True,
        )
        raise click.Abort()

    user = general.update("consumers", session, id_username, **payload)
    user = sort_dict(user)
    click.echo(tabulate([user], headers="keys", tablefmt=tablefmt))


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


@consumers_cli.group(name="key-auth")
def key_auth() -> None:
    """Manage key auths of Consumer Objects."""
    pass


@key_auth.command(name="list")
@click.argument("id_username")
@click.pass_context
def list_key_auths(ctx: click.Context, id_username: str) -> None:
    """List keys of one Consumer Object."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    key_auths = consumers.key_auths(session, id_username)
    key_auths = sort_dict(key_auths)
    for key in key_auths:
        parse_datetimes(key)
    click.echo(tabulate(key_auths, headers="keys", tablefmt=tablefmt))


@key_auth.command(name="add")
@click.option(
    "--key", help="The key to use. If not set, kong will auto-generate a key."
)
@click.argument("id_username")
@click.pass_context
def add_key_auth(ctx: click.Context, id_username: str, key: Optional[str]) -> None:
    """Add a key to one Consumer Object.

    **Note**: It is recommended to let Kong auto-generate the key. Only specify it
    yourself if you are migrating an existing system to Kong. You must re-use your
    keys to make the migration to Kong transparent to your Consumers.
    """
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    key_auth = consumers.add_key_auth(session, id_username, key)
    key_auth = sort_dict(key_auth)
    parse_datetimes(key_auth)
    click.echo(tabulate([key_auth], headers="keys", tablefmt=tablefmt))


@key_auth.command(name="delete")
@click.argument("id_username")
@click.argument("key_id", type=click.UUID)
@click.pass_context
def delete_key_auth(ctx: click.Context, id_username: str, key_id: UUID) -> None:
    """Delete a key."""
    session = ctx.obj["session"]

    consumers.delete_key_auth(session, id_username, str(key_id))
    click.echo(f"Deleted key `{key_id}` of consumer `{id_username}`!")


@key_auth.command(name="update")
@click.argument("id_username")
@click.argument("key_id", type=click.UUID)
@click.argument("new_key")
@click.pass_context
def update_key_auth(
    ctx: click.Context, id_username: str, key_id: UUID, new_key: str
) -> None:
    """Update a key of an Consumer Object."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    key_auth = consumers.update_key_auth(session, id_username, str(key_id), new_key)
    key_auth = sort_dict(key_auth)
    parse_datetimes(key_auth)
    click.echo(tabulate([key_auth], headers="keys", tablefmt=tablefmt))


@consumers_cli.group()
def basic_auth() -> None:
    """Manage basic auths of Consumer Objects."""
    pass


@basic_auth.command(name="list")
@click.argument("id_username")
@click.pass_context
def list_basic_auths(ctx: click.Context, id_username: str) -> None:
    """List basic-auths of one Consumer Object."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    basic_auths = consumers.basic_auths(session, id_username)
    basic_auths = sort_dict(basic_auths)
    for key in basic_auths:
        parse_datetimes(key)
    click.echo(tabulate(basic_auths, headers="keys", tablefmt=tablefmt))


@basic_auth.command(name="add")
@click.option("--username", help="The username.", required=True, prompt=True)
@click.option(
    "--password", help="The password.", required=True, prompt=True, hide_input=True
)
@click.argument("id_username")
@click.pass_context
def add_basic_auth(
    ctx: click.Context, id_username: str, username: str, password: str
) -> None:
    """Add basic-auth credentials to one Consumer Object."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    basic_auth = consumers.add_basic_auth(session, id_username, username, password)
    basic_auth = sort_dict(basic_auth)
    parse_datetimes(basic_auth)
    click.echo(tabulate([basic_auth], headers="keys", tablefmt=tablefmt))


@basic_auth.command(name="delete")
@click.argument("id_username")
@click.argument("basic_auth_id", type=click.UUID)
@click.pass_context
def delete_basic_auth(
    ctx: click.Context, id_username: str, basic_auth_id: UUID
) -> None:
    """Delete a basic-auth object."""
    session = ctx.obj["session"]

    consumers.delete_basic_auth(session, id_username, str(basic_auth_id))
    click.echo(f"Deleted credentials `{basic_auth_id}` of consumer `{id_username}`!")


@basic_auth.command(name="update")
@click.option("--username", help="The username.")
@click.option("--password", help="The password.")
@click.argument("id_username")
@click.argument("basic_auth_id", type=click.UUID)
@click.pass_context
def update_basic_auth(
    ctx: click.Context,
    id_username: str,
    basic_auth_id: UUID,
    username: Optional[str],
    password: Optional[str],
) -> None:
    """Update a basic-auth object of an Consumer Object.

    At least one of username or password has to be set.
    """
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    if not (username or password):
        click.echo(
            "You must set either `--username` or `--password` with the request.",
            err=True,
        )
        raise click.Abort()

    basic_auth = consumers.update_basic_auth(
        session, id_username, str(basic_auth_id), username, password
    )
    basic_auth = sort_dict(basic_auth)
    parse_datetimes(basic_auth)
    click.echo(tabulate([basic_auth], headers="keys", tablefmt=tablefmt))
