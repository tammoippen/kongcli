from typing import Any, Dict, Optional, Tuple, Union

import click

from ._session import LiveServerSession
from ._util import dict_from_dot, json_dumps


@click.command()
@click.option(
    "--dry-run", is_flag=True, help="Only create the request without sending it."
)
@click.option("--header", "-H", type=(str, str), multiple=True, help="Add headers.")
@click.option(
    "--data",
    "-d",
    type=(str, str),
    multiple=True,
    help="Add key-value data points to the payload.",
)
@click.argument("method")
@click.argument("url")
@click.pass_context
def raw(
    ctx: click.Context,
    method: str,
    url: str,
    header: Tuple[Tuple[str, str], ...],
    data: Tuple[Tuple[str, str], ...],
    dry_run: bool,
) -> None:
    """Perform raw http requests to kong.

    You can provide headers using the --header / -H option:

    \b
    - to get the header 'Accept: application/json' use
        -H Accept application/json
    - to get the header 'Content-Type: application/json; charset=utf-8' use
        -H Content-Type "application/json; charset=utf-8"

    \b
    You can provide a json body using the --data / -d option
      -d foo bar          # => {"foo": "bar"}
      -d foo true         # => {"foo": true}
      -d foo '"true"'     # => {"foo": "true"}
      -d foo.bar.baz 2.3  # => {"foo": {"bar": {"baz": 2.3}}}
      -d name bar -d config.methods '["GET", "POST"]'
      # => {"name": "bar", "config": {"methods": ["GET", "POST"]}}

    The first argument to `--data / -d` is the key. It is split by dots
    and sub-dictionaries are created. The second argument is assumed to be
    valid JSON; if it cannot be parsed, we assume it is a string. Multiple
    usages of `--data / -d` will merge the dictionary.
    """
    session: LiveServerSession = ctx.obj["session"]
    headers_dict = {h[0]: h[1] for h in header}
    click.echo(f"> {method} {session.prefix_url}{url}", err=True)
    for k, v in {**session.headers, **headers_dict}.items():
        click.echo(f"> {k}: {v}", err=True)
    click.echo(">", err=True)

    payload: Optional[Union[str, Dict[str, Any]]] = None
    if data:
        payload = dict_from_dot(data)
    if payload:
        payload = json_dumps(payload)
        headers_dict["content-type"] = "application/json"
        click.echo("> Body:", err=True)
        click.echo(f"> {payload}", err=True)

    if dry_run:
        click.echo("---<<== Done with dry-run. ==>>---")
        return

    resp = session.request(method, url, headers=headers_dict, data=payload)
    click.echo(f"\n< http/{resp.raw.version} {resp.status_code} {resp.reason}", err=True)
    for k, v in resp.headers.items():
        click.echo(f"< {k}: {v}", err=True)
    click.echo(err=True)
    click.echo(resp.text)
