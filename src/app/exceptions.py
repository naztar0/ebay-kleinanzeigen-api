from __future__ import annotations


class KleinanzeigenBannedError(Exception):
    """Raised when Kleinanzeigen temporarily blocks the server's IP range.

    Kleinanzeigen returns a German-language HTML error page ("IP-Bereich
    vorübergehend gesperrt") when a specific IP range has been flagged for
    unusual activity.  The block is temporary and usually lifts within a
    few hours.
    """
