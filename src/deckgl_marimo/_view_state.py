"""ViewState dataclass for deckgl-marimo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ViewState:
    """Represents the map camera state.

    Parameters
    ----------
    longitude : float
        Center longitude.
    latitude : float
        Center latitude.
    zoom : float
        Zoom level (0-22).
    pitch : float
        Tilt angle in degrees (0-85).
    bearing : float
        Rotation angle in degrees.
    """

    longitude: float = 0.0
    latitude: float = 0.0
    zoom: float = 1.0
    pitch: float = 0.0
    bearing: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for traitlet serialization."""
        return {
            "longitude": self.longitude,
            "latitude": self.latitude,
            "zoom": self.zoom,
            "pitch": self.pitch,
            "bearing": self.bearing,
        }
