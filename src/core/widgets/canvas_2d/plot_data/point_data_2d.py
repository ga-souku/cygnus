"""Point data for 2D plotting."""

from src.util.logger import Logger
from .base_2d_plot_data import Base2DPlotData
from .plot_data_2d_enum import PlotData2D


log = Logger(__name__)

class PointData2D(Base2DPlotData):
    """Represents a single point in 2D space."""

    def __init__(self, id: str, x: float, y: float, color: str = "r", deletable: bool = True, update: bool = True):
        """
        Initialize a 2D point.

        :param id: Unique identifier for the point
        :param x: X coordinate
        :param y: Y coordinate
        :param color: Color string (default: 'r')
        :param deletable: Whether this point can be deleted (default: True)
        :param update: Whether this point needs to be updated in the UI (default: True)
        """
        super().__init__(id, color, PlotData2D.POINT, update)
        self._x = x
        self._y = y
        self._deletable = deletable
        
        log.d(f"Created point at ({x}, {y}) with id: {id}, deletable: {deletable}")

    @property
    def x(self) -> float:
        """Get the X coordinate."""
        return self._x

    @x.setter
    def x(self, value: float):
        """Set the X coordinate."""
        log.d(f"Setting x from {self._x} to {value}")
        self._x = value
        self._update = True

    @property
    def y(self) -> float:
        """Get the Y coordinate."""
        return self._y

    @y.setter
    def y(self, value: float):
        """Set the Y coordinate."""
        log.d(f"Setting y from {self._y} to {value}")
        self._y = value
        self._update = True

    @property
    def deletable(self) -> bool:
        """Get whether this point can be deleted."""
        return self._deletable

    @deletable.setter
    def deletable(self, value: bool):
        """Set whether this point can be deleted."""
        log.d(f"Setting deletable from {self._deletable} to {value}")
        self._deletable = value

    def distance_to(self, x: float, y: float) -> float:
        """
        Calculate Euclidean distance to another point.

        :param x: X coordinate of the other point
        :param y: Y coordinate of the other point
        :return: Euclidean distance
        """
        return ((self._x - x) ** 2 + (self._y - y) ** 2) ** 0.5
