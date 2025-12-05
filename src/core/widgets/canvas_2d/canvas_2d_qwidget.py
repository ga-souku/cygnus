"""2D Canvas widget using PyQtGraph."""

from typing import Dict

import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout

from src.util.logger import Logger

from .canvas_2d_qviewmodel import Canvas2DQViewModel
from .plot_data.base_2d_plot_data import Base2DPlotData
from .plot_data.canvas_2d_plot_data import Canvas2DPlotData
from .plot_data.plot_data_2d_enum import PlotData2D
from .plot_data.point_data_2d import PointData2D
from .plot_data.polygon_data_2d import PolygonData2D
from .plot_data.polyline_data_2d import PolylineData2D



log = Logger(__name__)

class Canvas2DQWidget(QWidget):
    """2D Canvas widget using PyQtGraph for rendering."""

    def __init__(self, view_model: Canvas2DQViewModel, parent=None):
        """
        Initialize the canvas widget.

        :param view_model: ViewModel instance to observe
        :param parent: Parent widget
        """
        super().__init__(parent)
        self._view_model = view_model
        
        # Create PyQtGraph plot widget
        self._plot_widget = pg.PlotWidget(parent=self)
        self._plot_widget.setLabel("left", "Y")
        self._plot_widget.setLabel("bottom", "X")
        self._plot_widget.showGrid(True, True)
        
        # Set initial x and y limits to 0-100
        self._plot_widget.setXRange(0, 100)
        self._plot_widget.setYRange(0, 100)
        
        # Store plot items for tracking
        self._plot_items: Dict[str, pg.GraphicsObject] = {}
        
        # Connect to view model update signal
        self._view_model.update_requested.connect(self.update)
        
        # Set up layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot_widget)
        self.setLayout(layout)
        
        log.d("Initialized Canvas2DQWidget")

    def update(self):
        """
        Update the UI by rendering all plot data that needs updating.
        
        This method gets the Canvas2DPlotData instance from the view model,
        filters plot data where update==True, and updates the UI accordingly.
        """
        log.d("Update method called")
        
        plot_data: Canvas2DPlotData = self._view_model.plot_data
        plots_to_update = plot_data.get_plots_to_update()
        
        log.d(f"Updating {len(plots_to_update)} plots")
        
        # Update or create plot items
        for plot in plots_to_update:
            self._render_plot(plot)
        
        # Remove plots that no longer exist
        existing_plot_ids = {plot.id for plot in plot_data.get_all_plots()}
        plot_ids_to_remove = set(self._plot_items.keys()) - existing_plot_ids
        
        for plot_id in plot_ids_to_remove:
            log.d(f"Removing plot item {plot_id}")
            item = self._plot_items.pop(plot_id)
            self._plot_widget.removeItem(item)
        
        # Mark all plots as updated
        plot_data.mark_all_updated()
        
        log.d("Update completed")

    def _render_plot(self, plot: Base2DPlotData):
        """
        Render a single plot item.

        :param plot: Plot data to render
        """
        plot_id = plot.id
        
        # Remove existing item if it exists
        if plot_id in self._plot_items:
            log.d(f"Removing existing plot item {plot_id}")
            item = self._plot_items.pop(plot_id)
            self._plot_widget.removeItem(item)
        
        # Create new plot item based on type
        if plot.type == PlotData2D.POINT and isinstance(plot, PointData2D):
            self._render_point(plot)
        
        elif plot.type == PlotData2D.POLYLINE and isinstance(plot, PolylineData2D):
            self._render_polyline(plot)
        
        elif plot.type == PlotData2D.POLYGON and isinstance(plot, PolygonData2D):
            self._render_polygon(plot)
        
        else:
            log.w(f"Unknown plot type: {plot.type}")

    def _render_point(self, point: PointData2D):
        """
        Render a point.

        :param point: Point data to render
        """
        log.d(f"Rendering point {point.id} at ({point.x}, {point.y})")
        
        # Create scatter plot item for point
        scatter = pg.ScatterPlotItem(
            [point.x],
            [point.y],
            pen=pg.mkPen(color=point.color, width=2),
            brush=pg.mkBrush(color=point.color),
            size=10,
            symbol="o"
        )
        
        self._plot_widget.addItem(scatter)
        self._plot_items[point.id] = scatter

    def _render_polyline(self, polyline: PolylineData2D):
        """
        Render a polyline.

        :param polyline: Polyline data to render
        """
        log.d(f"Rendering polyline {polyline.id} with {len(polyline.points)} points")
        
        # Extract x and y coordinates
        x_data, y_data = zip(*[(p.x, p.y) for p in polyline.points])
        
        if len(polyline.points) >= 2:
            # Create plot item for polyline (line connecting points)
            plot_item = pg.PlotDataItem(
                x_data,
                y_data,
                pen=pg.mkPen(color=polyline.color, width=2),
                symbol="o",
                symbolBrush=pg.mkBrush(color=polyline.color),
                symbolSize=6
            )
            
            self._plot_widget.addItem(plot_item)
            self._plot_items[polyline.id] = plot_item
        else:
            # If less than 2 points, just show the points as scatter
            if len(polyline.points) > 0:
                scatter = pg.ScatterPlotItem(
                    x_data,
                    y_data,
                    pen=pg.mkPen(color=polyline.color, width=2),
                    brush=pg.mkBrush(color=polyline.color),
                    size=6,
                    symbol="o"
                )
                
                self._plot_widget.addItem(scatter)
                self._plot_items[polyline.id] = scatter

    def _render_polygon(self, polygon: PolygonData2D):
        """
        Render a polygon.

        :param polygon: Polygon data to render
        """
        log.d(f"Rendering polygon {polygon.id} with {len(polygon.points)} points")
        
        # Extract x and y coordinates
        x_data, y_data = zip(*[(p.x, p.y) for p in polygon.points])
        
        if len(polygon.points) >= 3:
            # Remove duplicate closing point for display (if present)
            if len(x_data) > 1 and x_data[0] == x_data[-1] and y_data[0] == y_data[-1]:
                x_display = x_data[:-1]
                y_display = y_data[:-1]
            else:
                x_display = x_data
                y_display = y_data
            
            # Use PlotDataItem with connect='all' to create closed polygon outline
            plot_item = pg.PlotDataItem(
                x_display + [x_display[0]] if len(x_display) > 0 else [],  # Ensure closed
                y_display + [y_display[0]] if len(y_display) > 0 else [],  # Ensure closed
                pen=pg.mkPen(color=polygon.color, width=2),
                symbol="o",
                symbolBrush=pg.mkBrush(color=polygon.color),
                symbolSize=6,
                connect="all"  # Connect all points to close the polygon
            )
            
            self._plot_widget.addItem(plot_item)
            self._plot_items[polygon.id] = plot_item
        else:
            # If less than 3 points, just show the points as scatter
            if len(polygon.points) > 0:
                scatter = pg.ScatterPlotItem(
                    x_data,
                    y_data,
                    pen=pg.mkPen(color=polygon.color, width=2),
                    brush=pg.mkBrush(color=polygon.color),
                    size=6,
                    symbol="o"
                )
                
                self._plot_widget.addItem(scatter)
                self._plot_items[polygon.id] = scatter

    @property
    def view_model(self) -> Canvas2DQViewModel:
        """Get the view model."""
        return self._view_model

    @property
    def plot_widget(self) -> pg.PlotWidget:
        """Get the underlying PyQtGraph plot widget."""
        return self._plot_widget

    def get_plot_data(self) -> Canvas2DPlotData:
        """
        Get the current plot data container.

        :return: Canvas2DPlotData instance
        """
        return self._view_model.plot_data
