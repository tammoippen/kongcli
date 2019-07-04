import json
import sys
from typing import Tuple

import click

from ._session import LiveServerSession
from ._util import dict_from_dot


@click.command()
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
) -> None:
    """Perform raw http requests to kong.

    You can provide headers using the --header / -H option:

    - to get the header 'Accept: application/json' use

        -H Accept application/json

    - to get the header 'Content-Type: application/json; charset=utf-8' use

        -H Content-Type "application/json; charset=utf-8"

    You can provide a json body using the --data / -d option

      -d foo bar          # => {"foo": "bar"}

      -d foo true         # => {"foo": true}

      -d foo '"true"'     # => {"foo": "true"}

      -d foo.bar.baz 2.3  # => {"foo": {"bar": {"baz": 2.3}}}

      -d name bar -d config.methods '["GET", "POST"]'

      # => {"name": "bar", "config": {"methods": ["GET", "POST"]}}

    If first argument to `--data / -d` is the key. It is split by dots
    and sub-dictionaries are created. The second argument is assumed to be
    valid JSON; if it cannot be parsed, we assume it is a string. Multiple
    usages of `--data / -d` will merge the dictionary.
    """
    session: LiveServerSession = ctx.obj["session"]
    headers_dict = {h[0]: h[1] for h in header}
    print(f"> {method} {session.prefix_url}{url}", file=sys.stderr)
    for k, v in session.headers.items():
        print("> ", k, ": ", v, sep="", file=sys.stderr)
    for k, v in headers_dict.items():
        print("> ", k, ": ", v, sep="", file=sys.stderr)
    print(">", file=sys.stderr)

    payload = None
    if data:
        payload = dict_from_dot(data)
    if payload:
        print("> Body:")
        print(">", json.dumps(payload))

    resp = session.request(method, url, headers=headers_dict, json=payload)
    print(f"< http/{resp.raw.version}", resp.status_code, resp.reason, file=sys.stderr)
    for k, v in resp.headers.items():
        print("< ", k, ": ", v, sep="", file=sys.stderr)
    print(file=sys.stderr)
    print(resp.text)
