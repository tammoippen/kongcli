import json
from operator import itemgetter
from typing import Optional, Tuple
from uuid import UUID

import click
from loguru import logger
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
@click.pass_context
def list_plugins(ctx: click.Context) -> None:
    """List all global plugins."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]
    font = ctx.obj["font"]

    print_figlet("Plugins", font=font, width=160)
    plugins = get("plugins", lambda: general.all_of("plugins", session))
    print(tabulate(plugins, headers="keys", tablefmt=tablefmt))


@click.command()
@click.argument("plugin_name")
@click.pass_context
def schema(ctx: click.Context, plugin_name: str) -> None:
    """Get the schema of a certain plugin."""
    session = ctx.obj["session"]
    print(json.dumps(plugins.schema(session, plugin_name), indent=2, sort_keys=True))


def _enable_basic_auth_on_resource(resource: str):
    assert resource in ("services", "routes", "global")

    @click.command(name=f"enable-basic-auth-on-{resource}")
    @click.option(
        "--enabled",
        type=bool,
        default=True,
        help="Whether this plugin will be applied.",
    )
    @click.option(
        "--hide_credentials",
        type=bool,
        default=False,
        help="An optional boolean value telling the plugin to show or hide the credential from the upstream service. If `True`, the plugin will strip the credential from the request (i.e. the Authorization header) before proxying it.",
    )
    @click.option(
        "--anonymous",
        type=click.UUID,
        help="An optional string (consumer uuid) value to use as an “anonymous” consumer if authentication fails. If empty (default), the request will fail with an authentication failure 4xx. Please note that this value must refer to the Consumer `id` attribute which is internal to Kong, and not its `custom_id`.",
    )
    @click.argument("id_name")
    @click.pass_context
    def enable_basic_auth(
        ctx: click.Context,
        id_name: str,
        enabled: bool,
        hide_credentials: bool,
        anonymous: Optional[UUID],
    ) -> None:
        """Enable the basic-auth plugin."""
        session = ctx.obj["session"]
        tablefmt = ctx.obj["tablefmt"]

        payload = {"enabled": enabled, "config": {"hide_credentials": hide_credentials}}
        if anonymous:
            payload["config"]["anonymous"] = str(anonymous)

        if resource != "global":
            plugin = plugins.enable_on(
                session, resource, id_name, "basic-auth", **payload
            )
        else:
            payload["name"] = "basic-auth"
            plugin = general.add("plugins", session, **payload)
        print(tabulate([plugin], headers="keys", tablefmt=tablefmt))

    return enable_basic_auth


enable_basic_auth_routes = _enable_basic_auth_on_resource("routes")
enable_basic_auth_services = _enable_basic_auth_on_resource("services")
enable_basic_auth_global = _enable_basic_auth_on_resource("global")


def _enable_key_auth_on_resource(resource: str):
    assert resource in ("services", "routes", "global")

    @click.command(name=f"enable-key-auth-on-{resource}")
    @click.option(
        "--enabled",
        type=bool,
        default=True,
        help="Whether this plugin will be applied.",
    )
    @click.option(
        "--key_names",
        multiple=True,
        help="Describes parameter names where the plugin will look for a key. The client must send the authentication key in one of those key names, and the plugin will try to read the credential from a header or the querystring parameter with the same name. (default: `apikey`)\n**note**: the key names may only contain [a-z], [A-Z], [0-9], [_] and [-]. Underscores are not permitted for keys in headers due to additional restrictions in the NGINX defaults.",
    )
    @click.option(
        "--key_in_body",
        type=bool,
        default=False,
        help="If enabled, the plugin will read the request body (if said request has one and its MIME type is supported) and try to find the key in it. Supported MIME types are `application/www-form-urlencoded`, `application/json`, and `multipart/form-data`.",
    )
    @click.option(
        "--hide_credentials",
        type=bool,
        default=False,
        help="An optional boolean value telling the plugin to show or hide the credential from the upstream service. If `True`, the plugin will strip the credential from the request (i.e. the Authorization header) before proxying it.",
    )
    @click.option(
        "--anonymous",
        type=click.UUID,
        help="An optional string (consumer uuid) value to use as an “anonymous” consumer if authentication fails. If empty (default), the request will fail with an authentication failure 4xx. Please note that this value must refer to the Consumer `id` attribute which is internal to Kong, and not its `custom_id`.",
    )
    @click.option(
        "--run_on_preflight",
        type=bool,
        default=True,
        help="A boolean value that indicates whether the plugin should run (and try to authenticate) on `OPTIONS` preflight requests, if set to `false` then `OPTIONS` requests will always be allowed.",
    )
    @click.argument("id_name", required=resource != "global")
    @click.pass_context
    def enable_key_auth(
        ctx: click.Context,
        id_name: str,
        enabled: bool,
        key_names: Tuple[str, ...],
        key_in_body: bool,
        hide_credentials: bool,
        anonymous: Optional[UUID],
        run_on_preflight: bool,
    ) -> None:
        """Enable the key-auth plugin."""
        session = ctx.obj["session"]
        tablefmt = ctx.obj["tablefmt"]

        payload = {
            "enabled": enabled,
            "config": {
                "hide_credentials": hide_credentials,
                "key_in_body": key_in_body,
                "run_on_preflight": run_on_preflight,
            },
        }
        if anonymous:
            payload["config"]["anonymous"] = str(anonymous)
        if key_names:
            payload["config"]["key_names"] = list(key_names)

        if resource != "global":
            plugin = plugins.enable_on(
                session, resource, id_name, "key-auth", **payload
            )
        else:
            payload["name"] = "key-auth"
            plugin = general.add("plugins", session, **payload)
        print(tabulate([plugin], headers="keys", tablefmt=tablefmt))

    return enable_key_auth


enable_key_auth_routes = _enable_key_auth_on_resource("routes")
enable_key_auth_services = _enable_key_auth_on_resource("services")
enable_key_auth_global = _enable_key_auth_on_resource("global")


def _enable_acl_on_resource(resource: str):
    assert resource in ("services", "routes", "global")

    @click.command(name=f"enable-acl-on-{resource}")
    @click.option(
        "--enabled",
        type=bool,
        default=True,
        help="Whether this plugin will be applied.",
    )
    @click.option(
        "--white",
        multiple=True,
        help="Arbitrary group names that are allowed to consume the Service or Route. One of `config.whitelist` or `config.blacklist` must be specified.",
    )
    @click.option(
        "--black",
        multiple=True,
        help="Arbitrary group names that are not allowed to consume the Service or Route. One of config.whitelist or config.blacklist must be specified.",
    )
    @click.option(
        "--hide_groups_header",
        type=bool,
        default=False,
        help="Flag which if enabled (true), prevents the `X-Consumer-Groups` header to be sent in the request to the upstream service. (ignored in 0.13.x)",
    )
    @click.argument("id_name", required=resource != "global")
    @click.pass_context
    def enable_acl(
        ctx: click.Context,
        id_name: str,
        enabled: bool,
        white: Tuple[str, ...],
        black: Tuple[str, ...],
        hide_groups_header: bool,
    ) -> None:
        """Enable the acl plugin.

        Note that the whitelist and blacklist models are mutually exclusive in their usage, as
        they provide complimentary approaches. That is, you cannot configure an ACL with both
        whitelist and blacklist configurations. An ACL with a whitelist provides a positive
        security model, in which the configured groups are allowed access to the resources,
        and all others are inherently rejected. By contrast, a blacklist configuration provides
        a negative security model, in which certain groups are explicitly denied access to
        the resource (and all others are inherently allowed)
        """
        session = ctx.obj["session"]
        tablefmt = ctx.obj["tablefmt"]

        payload = {
            "enabled": enabled,
            "config": {"hide_groups_header": hide_groups_header},
        }
        if white and black:
            logger.error(
                "Only one of whitelist (multiple `--white`) or blacklist (multiple `--black`) are allowed."
            )
            raise click.Abort()
        if not white and not black:
            logger.error(
                "One of whitelist (multiple `--white`) or blacklist (multiple `--black`) has to be set."
            )
            raise click.Abort()

        info = general.information()

        if info["version"].startswith("0.13"):
            payload["config"].pop("hide_groups_header")

        if white:
            payload["config"]["whitelist"] = list(white)
        if black:
            payload["config"]["blacklist"] = list(black)

        if resource != "global":
            plugin = plugins.enable_on(session, resource, id_name, "acl", **payload)
        else:
            payload["name"] = "acl"
            plugin = general.add("plugins", session, **payload)
        print(tabulate([plugin], headers="keys", tablefmt=tablefmt))

    return enable_acl


enable_acl_routes = _enable_acl_on_resource("routes")
enable_acl_services = _enable_acl_on_resource("services")
enable_acl_global = _enable_acl_on_resource("global")


@click.command()
@click.argument("uuid_id", type=click.UUID)
@click.pass_context
def delete(ctx: click.Context, uuid_id: UUID) -> None:
    """Delete the  given plugin."""
    session = ctx.obj["session"]

    general.delete("plugins", session, str(uuid_id))
    print(f"Deleted plugin `{uuid_id}`!")


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
plugins_cli.add_command(list_plugins, name="list")
plugins_cli.add_command(schema)
# plugins_cli.add_command(enable_basic_auth_routes)
# plugins_cli.add_command(enable_basic_auth_services)
plugins_cli.add_command(enable_basic_auth_global)
# plugins_cli.add_command(enable_key_auth_routes)
# plugins_cli.add_command(enable_key_auth_services)
plugins_cli.add_command(enable_key_auth_global)
# plugins_cli.add_command(enable_acl_routes)
# plugins_cli.add_command(enable_acl_services)
plugins_cli.add_command(enable_acl_global)
plugins_cli.add_command(delete)
