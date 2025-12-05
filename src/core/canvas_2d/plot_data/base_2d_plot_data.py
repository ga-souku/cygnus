"""Base class for 2D plot data."""

from abc import ABC

from .plot_data_2d_enum import PlotData2D
from src.util.logger import Logger


log = Logger(__name__)

class Base2DPlotData(ABC):
    """Base class for all 2D plot data types."""

    def __init__(self, id: str, color: str, type: PlotData2D, update: bool = True):
        """
        Initialize base plot data.

        :param id: Unique identifier for the plot data
        :param color: Color string (e.g., 'r', 'blue', '#FF0000')
        :param type: Plot data type from PlotData2D enum
        :param update: Whether this plot data needs to be updated in the UI
        """
        self._id = id
        self._color = color
        self._type = type
        self._update = update
        
        log.d(f"Created {type.value} plot data with id: {id}")

    @property
    def id(self) -> str:
        """Get the unique identifier."""
        return self._id

    @id.setter
    def id(self, value: str):
        """Set the unique identifier."""
        log.d(f"Setting id from {self._id} to {value}")
        self._id = value
        self._update = True

    @property
    def color(self) -> str:
        """Get the color."""
        return self._color

    @color.setter
    def color(self, value: str):
        """Set the color."""
        log.d(f"Setting color from {self._color} to {value}")
        self._color = value
        self._update = True

    @property
    def type(self) -> PlotData2D:
        """Get the plot data type."""
        return self._type

    @property
    def update(self) -> bool:
        """Get the update flag."""
        return self._update

    @update.setter
    def update(self, value: bool):
        """Set the update flag."""
        self._update = value
