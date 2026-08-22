"""Error type shared by the WFS modules."""

from __future__ import annotations


class WFSError(RuntimeError):
    """A WFS request failed (HTTP error, OWS ExceptionReport, bad payload).

    Attributes
    ----------
    status
        HTTP status code when the failure came from a response, else ``None``.
    code
        OGC ``exceptionCode`` (e.g. ``"InvalidParameterValue"``) when the
        server returned an ExceptionReport, else ``None``.
    locator
        OGC ``locator`` attribute when present.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        code: str | None = None,
        locator: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.locator = locator
