"""Polygon data for 2D plotting."""

from typing import List

from src.util.logger import Logger

from .base_2d_plot_data import Base2DPlotData
from .plot_data_2d_enum import PlotData2D
from .point_data_2d import PointData2D


log = Logger(__name__)

class PolygonData2D(Base2DPlotData):
    """Represents a polygon (closed shape) in 2D space."""

    def __init__(self, id: str, points: List[PointData2D] | None = None, color: str = "g", update: bool = True):
        """
        Initialize a 2D polygon.

        :param id: Unique identifier for the polygon
        :param points: List of points that form the polygon (default: empty list)
        :param color: Color string (default: 'g')
        :param update: Whether this polygon needs to be updated in the UI (default: True)
        """
        super().__init__(id, color, PlotData2D.POLYGON, update)
        self._points: List[PointData2D] = points if points is not None else []
        self._closed = False
        
        log.d(f"Created polygon with id: {id}, {len(self._points)} points")
        
        # Auto-close if we have 3 or more points
        if len(self._points) >= 3:
            self._ensure_closed()

    @property
    def points(self) -> List[PointData2D]:
        """Get the list of points."""
        return self._points

    @property
    def closed(self) -> bool:
        """Get whether the polygon is closed."""
        return self._closed

    def _ensure_closed(self):
        """Ensure the polygon is closed by adding the first point at the end if needed."""
        if len(self._points) >= 3 and not self._closed:
            # Check if the last point is the same as the first
            first_point = self._points[0]
            last_point = self._points[-1]
            
            if first_point.x != last_point.x or first_point.y != last_point.y:
                # Create a copy of the first point to close the ring
                closing_point = PointData2D(
                    id=f"{first_point.id}_close",
                    x=first_point.x,
                    y=first_point.y,
                    color=first_point.color,
                    deletable=False,
                    update=True
                )
                log.d(f"Auto-closing polygon {self._id} by adding closing point")
                self._points.append(closing_point)
            
            self._closed = True

    def add_point(self, point: PointData2D):
        """
        Add a point to the polygon.
        
        If the polygon is closed (has 3+ points), new points are inserted
        at the second-last position (before the closing point).

        :param point: Point to add
        """
        if self._closed and len(self._points) >= 3:
            # Insert at second-last position (before the closing point)
            insert_index = len(self._points) - 1
            log.d(f"Inserting point {point.id} at position {insert_index} in closed polygon {self._id}")
            self._points.insert(insert_index, point)
        else:
            log.d(f"Adding point {point.id} to polygon {self._id}")
            self._points.append(point)
            
            # Auto-close when we reach 3 points
            if len(self._points) >= 3:
                self._ensure_closed()
        
        self._update = True

    def remove_point(self, point_id: str) -> bool:
        """
        Remove a point from the polygon by its ID.
        
        If removing a point causes the polygon to have less than 3 points,
        it will be unclosed.

        :param point_id: ID of the point to remove
        :return: True if point was removed, False otherwise
        """
        for i, point in enumerate(self._points):
            if point.id == point_id:
                # Don't allow deletion of closing point directly
                if not point.deletable:
                    log.w(f"Cannot delete non-deletable point {point_id} from polygon {self._id}")
                    return False
                
                log.d(f"Removing point {point_id} from polygon {self._id}")
                del self._points[i]
                
                # If we have less than 3 points, unclose the polygon
                if len(self._points) < 3:
                    self._closed = False
                    # Remove closing point if it exists
                    if len(self._points) > 0:
                        last_point = self._points[-1]
                        if last_point.id.endswith("_close"):
                            self._points.pop()
                else:
                    # Re-ensure closure after removal
                    self._ensure_closed()
                
                self._update = True
                return True
        
        log.w(f"Point {point_id} not found in polygon {self._id}")
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
