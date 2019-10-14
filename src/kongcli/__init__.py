from functools import partial

import click

click.option = partial(click.option, show_default=True)  # type: ignore
