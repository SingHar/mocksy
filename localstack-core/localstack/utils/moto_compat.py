"""Differences between moto-ext (LocalStack's Moto build) and upstream moto.

mocksy runs with either package (issue #6). Import the names that differ from
here instead of from Moto directly.
"""

import moto.core.exceptions as _moto_exceptions

# moto-ext: RESTError. Upstream moto 5.2 renamed it to _RESTError.
RESTError: type[Exception] = getattr(_moto_exceptions, "RESTError", None) or getattr(
    _moto_exceptions, "_RESTError"
)


def is_moto_ext() -> bool:
    """True when the installed Moto is LocalStack's moto-ext build."""
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        distribution("moto-ext")
        return True
    except PackageNotFoundError:
        return False
