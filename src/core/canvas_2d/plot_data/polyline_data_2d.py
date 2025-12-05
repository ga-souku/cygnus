"""Polyline data for 2D plotting."""

from typing import List

from src.util.logger import Logger

from .base_2d_plot_data import Base2DPlotData
from .plot_data_2d_enum import PlotData2D
from .point_data_2d import PointData2D

log = Logger(__name__)


class PolylineData2D(Base2DPlotData):
    """Represents a polyline (connected line segments) in 2D space."""

    def __init__(self, id: str, points: List[PointData2D] | None = None, color: str = "b", update: bool = True):
        """
        Initialize a 2D polyline.

        :param id: Unique identifier for the polyline
        :param points: List of points that form the polyline (default: empty list)
        :param color: Color string (default: 'b')
        :param update: Whether this polyline needs to be updated in the UI (default: True)
        """
        super().__init__(id, color, PlotData2D.POLYLINE, update)
        self._points: List[PointData2D] = points if points is not None else []
        
        log.d(f"Created polyline with id: {id}, {len(self._points)} points")

    @property
    def points(self) -> List[PointData2D]:
        """Get the list of points."""
        return self._points

    def add_point(self, point: PointData2D):
        """
        Add a point to the polyline.

        :param point: Point to add
        """
        log.d(f"Adding point {point.id} to polyline {self._id}")
        self._points.append(point)
        self._update = True

    def remove_point(self, point_id: str) -> bool:
        """
        Remove a point from the polyline by its ID.

        :param point_id: ID of the point to remove
        :return: True if point was removed, False otherwise
        """
        for i, point in enumerate(self._points):
            if point.id == point_id:
                log.d(f"Removing point {point_id} from polyline {self._id}")
                del self._points[i]
                self._update = True
                return True
        log.w(f"Point {point_id} not found in polyline {self._id}")
        return False

    def get_point_by_id(self, point_id: str) -> PointData2D | None:
        """
        Get a point by its ID.

        :param point_id: ID of the point
        :return: PointData2D if found, None otherwise
        """
        for point in self._points:
            if point.id == point_id:
                return point
        return None
