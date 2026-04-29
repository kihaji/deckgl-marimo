"""Type aliases for deck.gl layer accessor parameters.

These aliases describe the accepted forms for ``get_*`` parameters across
all layer classes. They are intentionally loose unions — the goal is to
give IDEs, generators, and LLMs a clearer signature than ``Any`` rather
than to prove correctness.

Accepted forms for any ``get_*`` parameter
------------------------------------------

- A constant (e.g. ``[255, 0, 0, 255]`` or ``5.0``).
- A column name string (e.g. ``"population"``) — looked up per row.
- A list of column names for vector accessors (e.g. ``["lon", "lat"]``).
- A callable ``f(row) -> value``, materialized over the data at spec time.
- A :class:`~deckgl_marimo.ColorScale` instance (color accessors only).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence, Union

if TYPE_CHECKING:
    from deckgl_marimo._color_scale import ColorScale

# Scalar number, column name, list of values, or callable returning a scalar.
# Used for size/width/elevation/radius/weight/angle/text/icon-style accessors.
Accessor = Union[
    float,
    int,
    str,
    Sequence[Union[float, int]],
    Callable[[Mapping[str, Any]], Any],
]

# Coordinate-shaped accessor: column name, pair/triple of column names,
# or callable returning a coordinate sequence.
# Used for get_position, get_source_position, get_target_position, get_path,
# get_polygon, and similar geo-keyed accessors.
PositionAccessor = Union[
    str,
    Sequence[str],
    Callable[[Mapping[str, Any]], Sequence[float]],
]

# Color accessor: RGB(A) constant, column name, callable returning RGB(A),
# or a ColorScale instance.
ColorAccessor = Union[
    str,
    Sequence[int],
    Callable[[Mapping[str, Any]], Sequence[int]],
    "ColorScale",
]

__all__ = ["Accessor", "ColorAccessor", "PositionAccessor"]
