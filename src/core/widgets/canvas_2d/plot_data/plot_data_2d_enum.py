"""Enumeration for 2D plot data types."""

from enum import Enum


class PlotData2D(Enum):
    """Enumeration of 2D plot data types."""

    POINT = "point"
    POLYLINE = "polyline"
    POLYGON = "polygon"
