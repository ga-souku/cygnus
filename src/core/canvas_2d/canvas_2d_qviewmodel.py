"""ViewModel for 2D canvas widget."""

import uuid

from PySide6.QtCore import QObject, Signal

from src.util.logger import Logger

from .plot_data.canvas_2d_plot_data import Canvas2DPlotData
from .plot_data.plot_data_2d_enum import PlotData2D
from .plot_data.point_data_2d import PointData2D
from .plot_data.polygon_data_2d import PolygonData2D
from .plot_data.polyline_data_2d import PolylineData2D

log = Logger(__name__)


class Canvas2DQViewModel(QObject):
    """ViewModel for managing 2D canvas data and interactions."""

    # Signal emitted when the UI needs to be updated
    update_requested = Signal()

    def __init__(self):
        """Initialize the view model."""
        super().__init__()
        self._plot_data = Canvas2DPlotData()
        self._current_plot_type = PlotData2D.POINT
        self._current_plot_id: str | None = None
        
        # Connect plot data changes to update signal
        self._plot_data.data_changed.connect(self._on_data_changed)
        
        log.d("Initialized Canvas2DQViewModel")

    @property
    def plot_data(self) -> Canvas2DPlotData:
        """Get the plot data container."""
        return self._plot_data

    @property
    def current_plot_type(self) -> PlotData2D:
        """Get the current plot type."""
        return self._current_plot_type

    @current_plot_type.setter
    def current_plot_type(self, value: PlotData2D):
        """Set the current plot type."""
        log.d(f"Setting current plot type to {value.value}")
        self._current_plot_type = value
        self._current_plot_id = None

    def _on_data_changed(self):
        """Handle data changed signal from plot data."""
        log.d("Data changed, requesting UI update")
        self.update_requested.emit()

    def add_point(self, x: float, y: float):
        """
        Add a point at the specified coordinates.

        :param x: X coordinate
        :param y: Y coordinate
        """
        log.d(f"Adding point at ({x}, {y})")
        
        if self._current_plot_type == PlotData2D.POINT:
            # Create a new point plot
            point_id = f"point_{uuid.uuid4().hex[:8]}"
            point = PointData2D(point_id, x, y, color="r", deletable=True)
            self._plot_data.add_plot(point)
            log.d(f"Created new point plot: {point_id}")
        
        elif self._current_plot_type == PlotData2D.POLYLINE:
            # Add point to current polyline or create new one
            if self._current_plot_id is None:
                # Create new polyline
                self._current_plot_id = f"polyline_{uuid.uuid4().hex[:8]}"
                polyline = PolylineData2D(self._current_plot_id, color="b")
                self._plot_data.add_plot(polyline)
                log.d(f"Created new polyline: {self._current_plot_id}")
            
            polyline = self._plot_data.get_plot(self._current_plot_id)
            if isinstance(polyline, PolylineData2D):
                # Save state before adding point for undo support
                self._plot_data.save_state_for_undo()
                point_id = f"point_{uuid.uuid4().hex[:8]}"
                point = PointData2D(point_id, x, y, color=polyline.color, deletable=True)
                polyline.add_point(point)
                self._plot_data.data_changed.emit()
        
        elif self._current_plot_type == PlotData2D.POLYGON:
            # Add point to current polygon or create new one
            if self._current_plot_id is None:
                # Create new polygon
                self._current_plot_id = f"polygon_{uuid.uuid4().hex[:8]}"
                polygon = PolygonData2D(self._current_plot_id, color="g")
                self._plot_data.add_plot(polygon)
                log.d(f"Created new polygon: {self._current_plot_id}")
            
            polygon = self._plot_data.get_plot(self._current_plot_id)
            if isinstance(polygon, PolygonData2D):
                # Save state before adding point for undo support
                self._plot_data.save_state_for_undo()
                point_id = f"point_{uuid.uuid4().hex[:8]}"
                point = PointData2D(point_id, x, y, color=polygon.color, deletable=True)
                polygon.add_point(point)
                self._plot_data.data_changed.emit()

    def delete_point_near(self, x: float, y: float, threshold: float = 10.0) -> bool:
        """
        Delete a point near the specified coordinates.

        :param x: X coordinate
        :param y: Y coordinate
        :param threshold: Distance threshold in pixels (default: 10.0)
        :return: True if a point was deleted, False otherwise
        """
        log.d(f"Attempting to delete point near ({x}, {y}) with threshold {threshold}")
        
        # Search through all plots to find a deletable point within threshold
        for plot in self._plot_data.get_all_plots():
            if isinstance(plot, PointData2D):
                if plot.deletable and plot.distance_to(x, y) <= threshold:
                    log.d(f"Deleting point {plot.id}")
                    self._plot_data.remove_plot(plot.id)
                    return True
            
            elif isinstance(plot, (PolylineData2D, PolygonData2D)):
                for point in plot.points:
                    if point.deletable and point.distance_to(x, y) <= threshold:
                        log.d(f"Deleting point {point.id} from {plot.type.value} {plot.id}")
                        # Save state before deletion for undo support
                        self._plot_data.save_state_for_undo()
                        plot.remove_point(point.id)
                        self._plot_data.data_changed.emit()
                        return True
        
        log.d("No deletable point found within threshold")
        return False

    def undo(self):
        """Undo the last action."""
        log.d("Undo requested")
        if self._plot_data.undo():
            log.d("Undo successful")
        else:
            log.w("Undo failed - no undo available")

    def redo(self):
        """Redo the last undone action."""
        log.d("Redo requested")
        if self._plot_data.redo():
            log.d("Redo successful")
        else:
            log.w("Redo failed - no redo available")

    def clear_current_plot(self):
        """Clear the current plot (for polyline/polygon, allows starting a new one)."""
        log.d("Clearing current plot")
        self._current_plot_id = None
