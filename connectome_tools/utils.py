"""Common utilities."""
import logging
import sys
from functools import wraps

import psutil

L = logging.getLogger(__name__)

_help_link = (
    "https://bbpteam.epfl.ch/documentation/projects"
    "/connectome-tools/latest/index.html#troubleshooting"
)


def exit_if_not_alone():
    """Exit the program if there are other instances running on the same host."""
    attrs = ["pid", "name", "username", "cmdline"]
    this = psutil.Process().as_dict(attrs=attrs)
    others = [
        p.info
        for p in psutil.process_iter(attrs=attrs)
        if p.info["pid"] != this["pid"]
        and all(p.info[k] == this[k] for k in ["name", "username", "cmdline"])
    ]
    if others:
        L.error(
            "Only one instance can be executed at the same time! Exiting process with pid %s.\n"
            "See %s for more details.",
            this["pid"],
            _help_link,
        )
        sys.exit(1)


def runalone(func):
    """Decorator that terminates the process if other instances of the same program are running."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        exit_if_not_alone()
        return func(*args, **kwargs)

    return wrapper
