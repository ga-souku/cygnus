"""Canvas plot data container for managing all 2D plots."""

from typing import Dict, List

from PySide6.QtCore import QObject, Signal

from src.util.logger import Logger

from .base_2d_plot_data import Base2DPlotData
from .point_data_2d import PointData2D
from .polygon_data_2d import PolygonData2D
from .polyline_data_2d import PolylineData2D
from .plot_data_2d_enum import PlotData2D


class Canvas2DPlotData(QObject):
    """Container for all plot data in the 2D canvas."""

    # Signal emitted when plot data changes
    data_changed = Signal()

    def __init__(self):
        """Initialize the canvas plot data container."""
        super().__init__()
        self._plots: Dict[str, Base2DPlotData] = {}
        self._undo_stack: List[Dict[str, Base2DPlotData]] = []
        self._redo_stack: List[Dict[str, Base2DPlotData]] = []
        self._logger = Logger(self.__class__.__name__)
        self._logger.d("Initialized Canvas2DPlotData")

    def add_plot(self, plot: Base2DPlotData):
        """
        Add a plot to the canvas.

        :param plot: Plot data to add
        """
        self._logger.d(f"Adding plot {plot.id} of type {plot.type.value}")
        self._save_state_for_undo()
        self._plots[plot.id] = plot
        plot.update = True
        self.data_changed.emit()

    def remove_plot(self, plot_id: str) -> bool:
        """
        Remove a plot from the canvas.

        :param plot_id: ID of the plot to remove
        :return: True if plot was removed, False otherwise
        """
        if plot_id in self._plots:
            self._logger.d(f"Removing plot {plot_id}")
            self._save_state_for_undo()
            del self._plots[plot_id]
            self.data_changed.emit()
            return True
        self._logger.w(f"Plot {plot_id} not found")
        return False

    def get_plot(self, plot_id: str) -> Base2DPlotData | None:
        """
        Get a plot by its ID.

        :param plot_id: ID of the plot
        :return: Base2DPlotData if found, None otherwise
        """
        return self._plots.get(plot_id)

    def get_all_plots(self) -> List[Base2DPlotData]:
        """
        Get all plots.

        :return: List of all plot data
        """
        return list(self._plots.values())

    def get_plots_to_update(self) -> List[Base2DPlotData]:
        """
        Get all plots that need to be updated (update == True).

        :return: List of plot data that needs updating
        """
        plots_to_update = [plot for plot in self._plots.values() if plot.update]
        self._logger.d(f"Found {len(plots_to_update)} plots to update")
        return plots_to_update

    def mark_all_updated(self):
        """Mark all plots as updated (set update flag to False)."""
        for plot in self._plots.values():
            plot.update = False

    def save_state_for_undo(self):
        """
        Save current state for undo functionality.
        
        This is a public method that can be called before making changes
        that should be undoable.
        """
        self._save_state_for_undo()

    def _save_state_for_undo(self):
        """Save current state for undo functionality."""
        # Deep copy the current state
        state_copy = {}
        for plot_id, plot in self._plots.items():
            if isinstance(plot, PointData2D):
                state_copy[plot_id] = PointData2D(
                    plot.id, plot.x, plot.y, plot.color, plot.deletable, False
                )
            elif isinstance(plot, PolylineData2D):
                points_copy = [
                    PointData2D(p.id, p.x, p.y, p.color, p.deletable, False)
                    for p in plot.points
                ]
                state_copy[plot_id] = PolylineData2D(plot.id, points_copy, plot.color, False)
            elif isinstance(plot, PolygonData2D):
                points_copy = [
                    PointData2D(p.id, p.x, p.y, p.color, p.deletable, False)
                    for p in plot.points
                ]
                state_copy[plot_id] = PolygonData2D(plot.id, points_copy, plot.color, False)
        
        self._undo_stack.append(state_copy)
        # Limit undo stack size
        if len(self._undo_stack) > 100:
            self._undo_stack.pop(0)
        # Clear redo stack when new action is performed
        self._redo_stack.clear()
        self._logger.d(f"Saved state for undo. Stack size: {len(self._undo_stack)}")

    def undo(self) -> bool:
        """
        Undo the last action.

        :return: True if undo was successful, False if no undo available
        """
        if not self._undo_stack:
            self._logger.w("No undo available")
            return False
        
        self._logger.d("Performing undo")
        # Save current state to redo stack
        current_state = {}
        for plot_id, plot in self._plots.items():
            if isinstance(plot, PointData2D):
                current_state[plot_id] = PointData2D(
                    plot.id, plot.x, plot.y, plot.color, plot.deletable, False
                )
            elif isinstance(plot, PolylineData2D):
                points_copy = [
                    PointData2D(p.id, p.x, p.y, p.color, p.deletable, False)
                    for p in plot.points
                ]
                current_state[plot_id] = PolylineData2D(plot.id, points_copy, plot.color, False)
            elif isinstance(plot, PolygonData2D):
                points_copy = [
                    PointData2D(p.id, p.x, p.y, p.color, p.deletable, False)
                    for p in plot.points
                ]
                current_state[plot_id] = PolygonData2D(plot.id, points_copy, plot.color, False)
        
        self._redo_stack.append(current_state)
        
        # Restore previous state
        previous_state = self._undo_stack.pop()
        self._plots = previous_state
        # Mark all restored plots as needing update
        for plot in self._plots.values():
            plot.update = True
        self.data_changed.emit()
        return True

    def redo(self) -> bool:
        """
        Redo the last undone action.

        :return: True if redo was successful, False if no redo available
        """
        if not self._redo_stack:
            self._logger.w("No redo available")
            return False
        
        self._logger.d("Performing redo")
        # Save current state to undo stack
        current_state = {}
        for plot_id, plot in self._plots.items():
            if isinstance(plot, PointData2D):
                current_state[plot_id] = PointData2D(
                    plot.id, plot.x, plot.y, plot.color, plot.deletable, False
                )
            elif isinstance(plot, PolylineData2D):
                points_copy = [
                    PointData2D(p.id, p.x, p.y, p.color, p.deletable, False)
                    for p in plot.points
                ]
                current_state[plot_id] = PolylineData2D(plot.id, points_copy, plot.color, False)
            elif isinstance(plot, PolygonData2D):
                points_copy = [
                    PointData2D(p.id, p.x, p.y, p.color, p.deletable, False)
                    for p in plot.points
                ]
                current_state[plot_id] = PolygonData2D(plot.id, points_copy, plot.color, False)
        
        self._undo_stack.append(current_state)
        
        # Restore next state
        next_state = self._redo_stack.pop()
        self._plots = next_state
        # Mark all restored plots as needing update
        for plot in self._plots.values():
            plot.update = True
        self.data_changed.emit()
        return True

    def clear(self):
        """Clear all plots from the canvas."""
        self._logger.d("Clearing all plots")
        self._save_state_for_undo()
        self._plots.clear()
        self.data_changed.emit()
