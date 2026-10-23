"""Differences between moto-ext (LocalStack's Moto build) and upstream moto.

mocksy runs with either package (issue #6). Import the names that differ from
here instead of from Moto directly.
"""

import moto.core.exceptions as _moto_exceptions

# moto-ext: RESTError. Upstream moto 5.2 renamed it to _RESTError.
RESTError: type[Exception] = (
    getattr(_moto_exceptions, "RESTError", None) or _moto_exceptions._RESTError
)


def is_moto_ext() -> bool:
    """True when the installed Moto is LocalStack's moto-ext build."""
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        distribution("moto-ext")
        return True
    except PackageNotFoundError:
        return False


def to_moto_request(request, raw_url: str, full_raw_path: str):
    """Return the request in the form that the installed Moto dispatches.

    moto-ext takes mocksy's (werkzeug-based) request as it is. Upstream moto 5.2
    expects ``moto.core.request.Request``, which adds ``raw_path``, ``raw_url``
    and ``from_wsgi_server``; mocksy builds one from the method, URL, headers and
    body, keeps the undecoded path (``RAW_URI``), and marks it as coming from a
    WSGI server, as moto-ext treats werkzeug requests.
    """
    try:
        from moto.core.request import Request as MotoRequest
    except ImportError:
        return request
    if isinstance(request, MotoRequest):
        return request
    from rolo.request import restore_payload

    # restore_payload also covers a body that was read as form data, which empties get_data()
    moto_request = MotoRequest.from_primitives(
        request.method, raw_url, request.headers, body=restore_payload(request)
    )
    moto_request.environ["RAW_URI"] = full_raw_path
    moto_request.from_wsgi_server = True
    return moto_request
