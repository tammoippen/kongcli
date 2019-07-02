import json
from operator import itemgetter

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from .kong import general, plugins


@click.command()
@click.pass_context
def list_global_plugins(ctx: click.Context) -> None:
    """List all global plugins."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Global Plugins", font=font, width=160)

    plugins = ctx.obj.get("plugins", general.all_of("plugins", session))

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


@click.command()
@click.argument("plugin_name")
@click.pass_context
def schema(ctx: click.Context, plugin_name: str) -> None:
    """Get the schema of a certain plugin."""
    session = ctx.obj["session"]
    print(json.dumps(plugins.schema(session, plugin_name), indent=2, sort_keys=True))


@click.group(name="plugins")
def plugins_cli() -> None:
    """Manage plugins of kong.

    A Plugin entity represents a plugin configuration that will be executed during the
    HTTP request/response lifecycle. It is how you can add functionalities to Services
    that run behind Kong, like Authentication or Rate Limiting for example.
    """
    pass


plugins_cli.add_command(list_global_plugins, name="list-global")
plugins_cli.add_command(schema, name="schema")
