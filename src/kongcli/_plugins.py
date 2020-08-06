from operator import itemgetter
from typing import Any, Dict, Iterable, Optional, Tuple
from uuid import UUID

import click
from loguru import logger
from pyfiglet import print_figlet
from tabulate import tabulate

from ._util import get, json_pretty, parse_datetimes, sort_dict, substitude_ids
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
        substitude_ids(p)
        p = sort_dict(p)
        if (
            p.get("route.id") is None
            and p.get("service.id") is None
            and p.get("consumer.id") is None
        ):
            p["config"] = json_pretty(p["config"])
            parse_datetimes(p)
            data.append(p)

    click.echo(
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
    services = get("services", lambda: general.all_of("services", session))
    consumers = get("consumers", lambda: general.all_of("consumers", session))

    for p in plugins:
        substitude_ids(p)
        p = sort_dict(p)
        p["config"] = json_pretty(p["config"])
        parse_datetimes(p)
        service_id = p.get("service.id")
        if service_id:
            for s in services:
                if s["id"] == service_id:
                    p["service_name"] = s["name"]
                    break
        consumer_id = p.get("consumer.id")
        if consumer_id:
            for c in consumers:
                if c["id"] == consumer_id:
                    p["consumer_name"] = c["username"]
                    p["consumer_custom_id"] = c["custom_id"]
                    break

    click.echo(
        tabulate(
            sorted(plugins, key=itemgetter("name")), headers="keys", tablefmt=tablefmt
        )
    )


@click.command()
@click.argument("plugin_name")
@click.pass_context
def schema(ctx: click.Context, plugin_name: str) -> None:
    """Get the schema of a certain plugin."""
    session = ctx.obj["session"]
    click.echo(json_pretty(plugins.schema(session, plugin_name)))


def _enable_basic_auth_on_resource(resource: str) -> click.Command:
    assert resource in ("services", "routes", "global")

    @click.command(name=f"enable-basic-auth-on-{resource}")
    @click.option(
        "--not-enabled", is_flag=True, help="Whether this plugin will be applied.",
    )
    @click.option(
        "--hide_credentials",
        is_flag=True,
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
        not_enabled: bool,
        hide_credentials: bool,
        anonymous: Optional[UUID],
    ) -> None:
        """Enable the basic-auth plugin.

        Once applied, any user with a valid credential can access the resource. To restrict usage
        to only some of the authenticated users, also add the ACL plugin (not covered here) and
        create whitelist or blacklist groups of users.
        """
        session = ctx.obj["session"]
        tablefmt = ctx.obj["tablefmt"]

        payload: Dict[str, Any] = {
            "enabled": not not_enabled,
            "config": {"hide_credentials": hide_credentials},
        }
        if anonymous:
            payload["config"]["anonymous"] = str(anonymous)

        if resource != "global":
            plugin = plugins.enable_on(
                session, resource, id_name, "basic-auth", **payload
            )
        else:
            payload["name"] = "basic-auth"
            plugin = general.add("plugins", session, **payload)

        parse_datetimes(plugin)
        substitude_ids(plugin)
        plugin = sort_dict(plugin)
        plugin["config"] = json_pretty(plugin["config"])
        click.echo(tabulate([plugin], headers="keys", tablefmt=tablefmt))

    return enable_basic_auth


enable_basic_auth_routes = _enable_basic_auth_on_resource("routes")
enable_basic_auth_services = _enable_basic_auth_on_resource("services")
enable_basic_auth_global = _enable_basic_auth_on_resource("global")


@click.command(name="update-basic-auth")
@click.option("--enabled", type=bool, help="Whether this plugin will be applied.")
@click.option(
    "--hide_credentials",
    type=bool,
    help="Show or hide the credential from the upstream service. If `True`, the plugin will strip the credential from the request (i.e. the Authorization header) before proxying it.",
)
@click.option(
    "--anonymous",
    type=click.UUID,
    help="Consumer id to use as an “anonymous” consumer if authentication fails. If empty (default), the request will fail with an authentication failure 4xx. Please note that this value must refer to the Consumer `id` attribute which is internal to Kong, and not its `custom_id`.",
)
@click.option(
    "--service",
    type=click.UUID,
    help="The id of the Service which this plugin will target.",
)
@click.option(
    "--route",
    type=click.UUID,
    help="The id of the Route which this plugin will target.",
)
@click.argument("plugin_id", type=click.UUID)
@click.pass_context
def update_basic_auth(
    ctx: click.Context,
    enabled: Optional[bool],
    hide_credentials: Optional[bool],
    anonymous: Optional[UUID],
    service: Optional[UUID],
    route: Optional[UUID],
    plugin_id: UUID,
) -> None:
    """Update a basic-auth plugin."""
    session = ctx.obj["session"]
    tablefmt = ctx.obj["tablefmt"]

    payload: Dict[str, Any] = {}
    if enabled is not None:
        payload["enabled"] = enabled
    if hide_credentials is not None or anonymous or service or route:
        payload["config"] = {}
    if hide_credentials is not None:
        payload["config"]["hide_credentials"] = hide_credentials
    if anonymous:
        payload["config"]["anonymous"] = str(anonymous)
    if service:
        payload["config"]["service"] = str(service)
    if route:
        payload["config"]["route"] = str(route)

    if not payload:
        logger.info(f"No changes specified for `{plugin_id}`")
        plugin = general.retrieve("plugins", session, str(plugin_id))
    else:
        payload["name"] = "basic-auth"
        plugin = general.update("plugins", session, str(plugin_id), **payload)
    parse_datetimes(plugin)
    substitude_ids(plugin)
    plugin = sort_dict(plugin)
    plugin["config"] = json_pretty(plugin["config"])
    click.echo(tabulate([plugin], headers="keys", tablefmt=tablefmt))


def _enable_key_auth_on_resource(resource: str) -> click.Command:
    assert resource in ("services", "routes", "global")

    @click.command(name=f"enable-key-auth-on-{resource}")
    @click.option(
        "--not-enabled", is_flag=True, help="Whether this plugin will be applied.",
    )
    @click.option(
        "--key_names",
        multiple=True,
        help="Describes parameter names where the plugin will look for a key. The client must send the authentication key in one of those key names, and the plugin will try to read the credential from a header or the querystring parameter with the same name. (default: `apikey`)\n**note**: the key names may only contain [a-z], [A-Z], [0-9], [_] and [-]. Underscores are not permitted for keys in headers due to additional restrictions in the NGINX defaults.",
    )
    @click.option(
        "--key_in_body",
        is_flag=True,
        help="If enabled, the plugin will read the request body (if said request has one and its MIME type is supported) and try to find the key in it. Supported MIME types are `application/www-form-urlencoded`, `application/json`, and `multipart/form-data`.",
    )
    @click.option(
        "--hide_credentials",
        is_flag=True,
        help="An optional boolean value telling the plugin to show or hide the credential from the upstream service. If `True`, the plugin will strip the credential from the request (i.e. the Authorization header) before proxying it.",
    )
    @click.option(
        "--anonymous",
        type=click.UUID,
        help="An optional string (consumer uuid) value to use as an “anonymous” consumer if authentication fails. If empty (default), the request will fail with an authentication failure 4xx. Please note that this value must refer to the Consumer `id` attribute which is internal to Kong, and not its `custom_id`.",
    )
    @click.option(
        "--not_run_on_preflight",
        is_flag=True,
        help="A boolean value that indicates whether the plugin should run (and try to authenticate) on `OPTIONS` preflight requests, if set to `false` then `OPTIONS` requests will always be allowed.",
    )
    @click.argument("id_name", required=resource != "global")
    @click.pass_context
    def enable_key_auth(
        ctx: click.Context,
        id_name: str,
        not_enabled: bool,
        key_names: Tuple[str, ...],
        key_in_body: bool,
        hide_credentials: bool,
        anonymous: Optional[UUID],
        not_run_on_preflight: bool,
    ) -> None:
        """Enable the key-auth plugin.

        Once applied, any user with a valid credential can access the Service. To restrict
        usage to only some of the authenticated users, also add the ACL plugin (not covered
        here) and create whitelist or blacklist groups of users.
        """
        session = ctx.obj["session"]
        tablefmt = ctx.obj["tablefmt"]

        payload: Dict[str, Any] = {
            "enabled": not not_enabled,
            "config": {
                "hide_credentials": hide_credentials,
                "key_in_body": key_in_body,
                "run_on_preflight": not not_run_on_preflight,
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

        parse_datetimes(plugin)
        substitude_ids(plugin)
        plugin = sort_dict(plugin)
        plugin["config"] = json_pretty(plugin["config"])
        click.echo(tabulate([plugin], headers="keys", tablefmt=tablefmt))

    return enable_key_auth


enable_key_auth_routes = _enable_key_auth_on_resource("routes")
enable_key_auth_services = _enable_key_auth_on_resource("services")
enable_key_auth_global = _enable_key_auth_on_resource("global")
# TODO update KA


def _enable_acl_on_resource(resource: str) -> click.Command:
    assert resource in ("services", "routes", "global")

    @click.command(name=f"enable-acl-on-{resource}")
    @click.option(
        "--not-enabled", is_flag=True, help="Whether this plugin will be applied.",
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
        is_flag=True,
        help="Flag which if enabled (true), prevents the `X-Consumer-Groups` header to be sent in the request to the upstream service. (ignored in 0.13.x)",
    )
    @click.argument("id_name", required=resource != "global")
    @click.pass_context
    def enable_acl(
        ctx: click.Context,
        id_name: str,
        not_enabled: bool,
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

        payload: Dict[str, Any] = {
            "enabled": not not_enabled,
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

        info = general.information(session)

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

        parse_datetimes(plugin)
        substitude_ids(plugin)
        plugin = sort_dict(plugin)
        plugin["config"] = json_pretty(plugin["config"])
        click.echo(tabulate([plugin], headers="keys", tablefmt=tablefmt))

    return enable_acl


enable_acl_routes = _enable_acl_on_resource("routes")
enable_acl_services = _enable_acl_on_resource("services")
enable_acl_global = _enable_acl_on_resource("global")
# TODO update ACL


def _enable_rate_limiting_on_resource(resource: str) -> click.Command:
    assert resource in ("services", "routes", "consumers", "global")

    @click.command(name=f"enable-rate-limiting-on-{resource}")
    @click.option(
        "--not-enabled", is_flag=True, help="Whether this plugin will be applied.",
    )
    @click.option(
        "--second",
        type=click.INT,
        help="The amount of HTTP requests the developer can make per second. At least one limit must exist.",
    )
    @click.option(
        "--minute",
        type=click.INT,
        help="The amount of HTTP requests the developer can make per minute. At least one limit must exist.",
    )
    @click.option(
        "--hour",
        type=click.INT,
        help="The amount of HTTP requests the developer can make per hour. At least one limit must exist.",
    )
    @click.option(
        "--day",
        type=click.INT,
        help="The amount of HTTP requests the developer can make per day. At least one limit must exist.",
    )
    @click.option(
        "--month",
        type=click.INT,
        help="The amount of HTTP requests the developer can make per month. At least one limit must exist.",
    )
    @click.option(
        "--year",
        type=click.INT,
        help="The amount of HTTP requests the developer can make per year. At least one limit must exist.",
    )
    @click.option(
        "--limit_by",
        type=click.Choice(["consumer", "credential", "ip"]),
        help="The entity that will be used when aggregating the limits: consumer, credential, ip. If the consumer or the credential cannot be determined, the system will always fallback to ip.",
        default="consumer",
    )
    @click.option(
        "--policy",
        type=click.Choice(["local", "cluster", "redis"]),
        default="cluster",
        help="The rate-limiting policies to use for retrieving and incrementing the limits. Available values are local (counters will be stored locally in-memory on the node), cluster (counters are stored in the datastore and shared across the nodes) and redis (counters are stored on a Redis server and will be shared across the nodes). In case of DB-less mode, at least one of local or redis must be specified. Please refer Implementation Considerations for details on which policy should be used.",
    )
    @click.option(
        "--not-fault_tolerant",
        is_flag=True,
        help="A boolean value that determines if the requests should be proxied even if Kong has troubles connecting a third-party datastore. If true requests will be proxied anyways effectively disabling the rate-limiting function until the datastore is working again. If false then the clients will see 500 errors.",
    )
    @click.option(
        "--hide_client_headers",
        is_flag=True,
        help="Optionally hide informative response headers.",
    )
    @click.option(
        "--redis_host",
        type=str,
        help="When using the redis policy, this property specifies the address to the Redis server.",
    )
    @click.option(
        "--redis_port",
        type=int,
        help="When using the redis policy, this property specifies the port of the Redis server.",
        default=6379,
    )
    @click.option(
        "--redis_password",
        type=str,
        help="When using the redis policy, this property specifies the password to connect to the Redis server.",
    )
    @click.option(
        "--redis_timeout",
        type=int,
        help="When using the redis policy, this property specifies the timeout in milliseconds of any command submitted to the Redis server.",
        default=2000,
    )
    @click.option(
        "--redis_database",
        type=int,
        help="When using the redis policy, this property specifies Redis database to use.",
        default=0,
    )
    @click.argument("resource_id", required=resource != "global")
    @click.pass_context
    def enable_rate_limit(
        ctx: click.Context,
        resource_id: str,
        not_enabled: bool,
        second: Optional[int],
        minute: Optional[int],
        hour: Optional[int],
        day: Optional[int],
        month: Optional[int],
        year: Optional[int],
        limit_by: str,
        policy: str,
        not_fault_tolerant: bool,
        hide_client_headers: bool,
        redis_host: Optional[str],
        redis_port: int,
        redis_password: Optional[str],
        redis_timeout: int,
        redis_database: int,
    ) -> None:
        """Enable the rate-limiting plugin.

        Rate limit how many HTTP requests a developer can make in a given period of
        seconds, minutes, hours, days, months or years. If the underlying Service/Route
        has no authentication layer, the Client IP address will be used, otherwise the
        Consumer will be used if an authentication plugin has been configured.

        A plugin which is not associated to any Service, Route or Consumer is considered
        "global", and will be run on every request.
        """
        session = ctx.obj["session"]
        tablefmt = ctx.obj["tablefmt"]

        payload: Dict[str, Any] = {
            "enabled": not not_enabled,
            "config": {
                "hide_client_headers": hide_client_headers,
                "fault_tolerant": not not_fault_tolerant,
                "limit_by": limit_by,
                "policy": policy,
            },
        }

        if not (second or minute or hour or day or month or year):
            click.echo("At least one limit must exist.", err=True)
            raise click.Abort()

        if second:
            payload["config"]["second"] = second
        if minute:
            payload["config"]["minute"] = minute
        if hour:
            payload["config"]["hour"] = hour
        if day:
            payload["config"]["day"] = day
        if month:
            payload["config"]["month"] = month
        if year:
            payload["config"]["year"] = year

        if policy == "redis":
            if redis_host is None:
                click.echo("Provide the configuration for redis.", err=True)
                raise click.Abort()
            payload["config"].update(
                {
                    "redis_host": redis_host,
                    "redis_port": redis_port,
                    "redis_timeout": redis_timeout,
                    "redis_database": redis_database,
                }
            )
            if redis_password is not None:
                payload["config"]["redis_password"] = redis_password

        if resource != "global":
            plugin = plugins.enable_on(
                session, resource, resource_id, "rate-limiting", **payload
            )
        else:
            payload["name"] = "rate-limiting"
            plugin = general.add("plugins", session, **payload)

        parse_datetimes(plugin)
        substitude_ids(plugin)
        plugin = sort_dict(plugin)
        plugin["config"] = json_pretty(plugin["config"])
        click.echo(tabulate([plugin], headers="keys", tablefmt=tablefmt))

    return enable_rate_limit


enable_rate_limiting_routes = _enable_rate_limiting_on_resource("routes")
enable_rate_limiting_services = _enable_rate_limiting_on_resource("services")
enable_rate_limiting_consumers = _enable_rate_limiting_on_resource("consumers")
enable_rate_limiting_global = _enable_rate_limiting_on_resource("global")
# TODO update rate-limit


def _enable_response_ratelimiting_on_resource(resource: str) -> click.Command:
    assert resource in ("services", "routes", "consumers", "global")

    @click.command(name=f"enable-response-ratelimiting-on-{resource}")
    @click.option(
        "--not-enabled", is_flag=True, help="Whether this plugin will be applied.",
    )
    @click.option(
        "--second",
        type=(str, int),
        multiple=True,
        help="The amount of HTTP requests the developer can make per second. At least one limit must exist.",
    )
    @click.option(
        "--minute",
        type=(str, int),
        multiple=True,
        help="The amount of HTTP requests the developer can make per minute. At least one limit must exist.",
    )
    @click.option(
        "--hour",
        type=(str, int),
        multiple=True,
        help="The amount of HTTP requests the developer can make per hour. At least one limit must exist.",
    )
    @click.option(
        "--day",
        type=(str, int),
        multiple=True,
        help="The amount of HTTP requests the developer can make per day. At least one limit must exist.",
    )
    @click.option(
        "--month",
        type=(str, int),
        multiple=True,
        help="The amount of HTTP requests the developer can make per month. At least one limit must exist.",
    )
    @click.option(
        "--year",
        type=(str, int),
        multiple=True,
        help="The amount of HTTP requests the developer can make per year. At least one limit must exist.",
    )
    @click.option(
        "--header_name",
        type=str,
        help="The name of the response header used to increment the counters.",
        default="X-Kong-limit",
    )
    @click.option(
        "--block_on_first_violation",
        is_flag=True,
        help="A boolean value that determines if the requests should be blocked as soon as one limit is being exceeded. This will block requests that are supposed to consume other limits too.",
    )
    @click.option(
        "--limit_by",
        type=click.Choice(["consumer", "credential", "ip"]),
        help="The entity that will be used when aggregating the limits: consumer, credential, ip. If the consumer or the credential cannot be determined, the system will always fallback to ip.",
        default="consumer",
    )
    @click.option(
        "--policy",
        type=click.Choice(["local", "cluster", "redis"]),
        default="cluster",
        help="The response-ratelimiting policies to use for retrieving and incrementing the limits. Available values are local (counters will be stored locally in-memory on the node), cluster (counters are stored in the datastore and shared across the nodes) and redis (counters are stored on a Redis server and will be shared across the nodes). In case of DB-less mode, at least one of local or redis must be specified. Please refer Implementation Considerations for details on which policy should be used.",
    )
    @click.option(
        "--not-fault_tolerant",
        is_flag=True,
        help="A boolean value that determines if the requests should be proxied even if Kong has troubles connecting a third-party datastore. If true requests will be proxied anyways effectively disabling the response-ratelimiting function until the datastore is working again. If false then the clients will see 500 errors.",
    )
    @click.option(
        "--hide_client_headers",
        is_flag=True,
        help="Optionally hide informative response headers.",
    )
    @click.option(
        "--redis_host",
        type=str,
        help="When using the redis policy, this property specifies the address to the Redis server.",
    )
    @click.option(
        "--redis_port",
        type=int,
        help="When using the redis policy, this property specifies the port of the Redis server.",
        default=6379,
    )
    @click.option(
        "--redis_password",
        type=str,
        help="When using the redis policy, this property specifies the password to connect to the Redis server.",
    )
    @click.option(
        "--redis_timeout",
        type=int,
        help="When using the redis policy, this property specifies the timeout in milliseconds of any command submitted to the Redis server.",
        default=2000,
    )
    @click.option(
        "--redis_database",
        type=int,
        help="When using the redis policy, this property specifies Redis database to use.",
        default=0,
    )
    @click.argument("resource_id", required=resource != "global")
    @click.pass_context
    def enable_response_ratelimiting(
        ctx: click.Context,
        resource_id: str,
        not_enabled: bool,
        second: Iterable[Tuple[str, int]],
        minute: Iterable[Tuple[str, int]],
        hour: Iterable[Tuple[str, int]],
        day: Iterable[Tuple[str, int]],
        month: Iterable[Tuple[str, int]],
        year: Iterable[Tuple[str, int]],
        header_name: str,
        block_on_first_violation: bool,
        limit_by: str,
        policy: str,
        not_fault_tolerant: bool,
        hide_client_headers: bool,
        redis_host: Optional[str],
        redis_port: int,
        redis_password: Optional[str],
        redis_timeout: int,
        redis_database: int,
    ) -> None:
        """Enable the response-ratelimiting plugin.

        This plugin allows you to limit the number of requests a developer can make
        based on a custom response header returned by the upstream service. You can
        arbitrary set as many rate-limiting objects (or quotas) as you want and instruct
        Kong to increase or decrease them by any number of units. Each custom rate-limiting
        object can limit the inbound requests per seconds, minutes, hours, days, months or years.

        If the underlying Service/Route (or deprecated API entity) has no authentication
        layer, the Client IP address will be used, otherwise the Consumer will be
        used if an authentication plugin has been configured.

        Kong API expects the limits to be set like:

        \b
        config.limits.{limit_name}   This is a list of custom objects that you can set,
                                     with arbitrary names set in the {limit_name} placeholder,
                                     like config.limits.sms.minute=20 if your object is called “SMS”.

        \b
        kongcli syntax is, using the options for the interval like:
            `--minute sms 20`
            `--{interval} {limit_name} {limit}`.
        """
        session = ctx.obj["session"]
        tablefmt = ctx.obj["tablefmt"]

        payload: Dict[str, Any] = {
            "enabled": not not_enabled,
            "config": {
                "hide_client_headers": hide_client_headers,
                "fault_tolerant": not not_fault_tolerant,
                "limit_by": limit_by,
                "policy": policy,
                "header_name": header_name,
                "block_on_first_violation": block_on_first_violation,
                "limits": {},
            },
        }

        if not (second or minute or hour or day or month or year):
            click.echo("At least one limit must exist.", err=True)
            raise click.Abort()

        for name, limits in [
            ("second", second),
            ("minute", minute),
            ("hour", hour),
            ("day", day),
            ("month", month),
            ("year", year),
        ]:
            for limit_name, limit in limits:
                if limit_name not in payload["config"]["limits"]:
                    payload["config"]["limits"][limit_name] = {}
                payload["config"]["limits"][limit_name][name] = limit

        if policy == "redis":
            if redis_host is None:
                click.echo("Provide the configuration for redis.", err=True)
                raise click.Abort()
            payload["config"].update(
                {
                    "redis_host": redis_host,
                    "redis_port": redis_port,
                    "redis_timeout": redis_timeout,
                    "redis_database": redis_database,
                }
            )
            if redis_password is not None:
                payload["config"]["redis_password"] = redis_password

        if resource != "global":
            plugin = plugins.enable_on(
                session, resource, resource_id, "response-ratelimiting", **payload
            )
        else:
            payload["name"] = "response-ratelimiting"
            plugin = general.add("plugins", session, **payload)

        parse_datetimes(plugin)
        substitude_ids(plugin)
        plugin = sort_dict(plugin)
        plugin["config"] = json_pretty(plugin["config"])
        click.echo(tabulate([plugin], headers="keys", tablefmt=tablefmt))

    return enable_response_ratelimiting


enable_response_ratelimiting_routes = _enable_response_ratelimiting_on_resource(
    "routes"
)
enable_response_ratelimiting_services = _enable_response_ratelimiting_on_resource(
    "services"
)
enable_response_ratelimiting_consumers = _enable_response_ratelimiting_on_resource(
    "consumers"
)
enable_response_ratelimiting_global = _enable_response_ratelimiting_on_resource(
    "global"
)
# TODO update response-ratelimiting


def _enable_request_size_limiting_on_resource(resource: str) -> click.Command:
    assert resource in ("services", "routes", "consumers", "global")

    @click.command(name=f"enable-request-size-limiting-on-{resource}")
    @click.option(
        "--not-enabled", is_flag=True, help="Whether this plugin will be applied.",
    )
    @click.option(
        "--allowed_payload_size",
        type=int,
        help="Allowed request payload size in megabytes, default is 128 (128000000 Bytes)",
        default=128,
    )
    @click.argument("id_name", required=resource != "global")
    @click.pass_context
    def request_size_limiting(
        ctx: click.Context, id_name: str, not_enabled: bool, allowed_payload_size: int
    ) -> None:
        """Enable the request-size-limiting plugin.

        Block incoming requests whose body is greater than a specific size in megabytes.

        \b
        *Note*: For security reasons we suggest enabling this plugin for any
                Service you add to Kong to prevent a DOS (Denial of Service)
                attack.
        """
        session = ctx.obj["session"]
        tablefmt = ctx.obj["tablefmt"]

        payload: Dict[str, Any] = {
            "enabled": not not_enabled,
            "config": {"allowed_payload_size": allowed_payload_size},
        }

        if resource != "global":
            plugin = plugins.enable_on(
                session, resource, id_name, "request-size-limiting", **payload
            )
        else:
            payload["name"] = "request-size-limiting"
            plugin = general.add("plugins", session, **payload)

        parse_datetimes(plugin)
        substitude_ids(plugin)
        plugin = sort_dict(plugin)
        plugin["config"] = json_pretty(plugin["config"])
        click.echo(tabulate([plugin], headers="keys", tablefmt=tablefmt))

    return request_size_limiting


enable_request_size_limiting_routes = _enable_request_size_limiting_on_resource(
    "routes"
)
enable_request_size_limiting_services = _enable_request_size_limiting_on_resource(
    "services"
)
enable_request_size_limiting_consumers = _enable_request_size_limiting_on_resource(
    "consumers"
)
enable_request_size_limiting_global = _enable_request_size_limiting_on_resource(
    "global"
)
# TODO update Request Size Limiting


@click.command()
@click.argument("uuid_id", type=click.UUID)
@click.pass_context
def delete(ctx: click.Context, uuid_id: UUID) -> None:
    """Delete the  given plugin."""
    session = ctx.obj["session"]

    general.delete("plugins", session, str(uuid_id))
    click.echo(f"Deleted plugin `{uuid_id}`!")


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
plugins_cli.add_command(update_basic_auth)
# plugins_cli.add_command(enable_key_auth_routes)
# plugins_cli.add_command(enable_key_auth_services)
plugins_cli.add_command(enable_key_auth_global)
# plugins_cli.add_command(enable_acl_routes)
# plugins_cli.add_command(enable_acl_services)
plugins_cli.add_command(enable_acl_global)
plugins_cli.add_command(enable_rate_limiting_global)
plugins_cli.add_command(enable_response_ratelimiting_global)
plugins_cli.add_command(enable_request_size_limiting_global)
plugins_cli.add_command(delete)
