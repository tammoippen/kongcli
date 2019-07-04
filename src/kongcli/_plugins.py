import json
from operator import itemgetter

import click
from pyfiglet import print_figlet
from tabulate import tabulate

from ._util import get
from .kong import general, plugins


@click.command()
@click.pass_context
def list_global_plugins(ctx: click.Context) -> None:
    """List all global plugins."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Global Plugins", font=font, width=160)

    plugins = get("plugins", lambda: general.all_of("plugins", session))

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
    """Manage Plugin Objects.

    A Plugin entity represents a plugin configuration that will be executed during the
    HTTP request/response lifecycle. It is how you can add functionalities to Services
    that run behind Kong, like Authentication or Rate Limiting for example. You can find
    more information about how to install and what values each plugin takes by visiting
    the [Kong Hub](https://docs.konghq.com/hub/).

    When adding a Plugin Configuration to a Service, every request made by a client
    to that Service will run said Plugin. If a Plugin needs to be tuned to
    different values for some specific Consumers, you can do so by specifying
    the consumer_id value

    Precedence

    A plugin will always be run once and only once per request. But the configuration
    with which it will run depends on the entities it has been configured for.

    Plugins can be configured for various entities, combination of entities, or even
    globally. This is useful, for example, when you wish to configure a plugin a
    certain way for most requests, but make authenticated requests behave slightly differently.

    Therefore, there exists an order of precedence for running a plugin when it has
    been applied to different entities with different configurations. The rule of thumb is:
    the more specific a plugin is with regards to how many entities it has been
    configured on, the higher its priority.
    """
    pass


plugins_cli.add_command(list_global_plugins, name="list-global")
plugins_cli.add_command(schema, name="schema")
