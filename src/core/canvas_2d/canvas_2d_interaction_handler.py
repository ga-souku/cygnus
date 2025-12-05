"""Interaction handler for 2D canvas widget."""

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent

from .canvas_2d_qviewmodel import Canvas2DQViewModel
from src.util.logger import Logger

log = Logger(__name__)


class Canvas2DInteractionHandler(QObject):
    """Handles user interactions with the canvas using eventFilter."""

    def __init__(self, view_model: Canvas2DQViewModel, plot_widget):
        """
        Initialize the interaction handler.

        :param view_model: ViewModel to forward interactions to
        :param plot_widget: PyQtGraph plot widget to filter events for
        """
        super().__init__()
        self._view_model = view_model
        self._plot_widget = plot_widget
        
        
        # Track mouse drag state
        self._is_dragging = False
        self._drag_start_pos = None
        
        # Install event filter on plot widget
        self._plot_widget.installEventFilter(self)
        
        log.d("Initialized Canvas2DInteractionHandler")

    def eventFilter(self, obj, event) -> bool:
        """
        Filter events for the plot widget.

        :param obj: Object that received the event
        :param event: Event object
        :return: True if event was handled, False otherwise
        """
        if obj != self._plot_widget:
            return False
        
        # Handle mouse events
        if isinstance(event, QMouseEvent):
            return self._handle_mouse_event(event)
        
        # Handle wheel events (for zoom)
        elif isinstance(event, QWheelEvent):
            return self._handle_wheel_event(event)
        
        # Handle key events (for undo/redo)
        elif isinstance(event, QKeyEvent):
            return self._handle_key_event(event)
        
        return False

    def _handle_mouse_event(self, event: QMouseEvent) -> bool:
        """
        Handle mouse events.

        :param event: Mouse event
        :return: True if event was handled, False otherwise
        """
        # Get mouse position in plot coordinates
        pos = event.position()
        view_box = self._plot_widget.getViewBox()
        scene_pos = view_box.mapSceneToView(pos)
        x, y = scene_pos.x(), scene_pos.y()
        
        if event.type() == QMouseEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                modifiers = event.modifiers()
                
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    # Ctrl+LeftClick: Delete point
                    log.d(f"Ctrl+LeftClick at ({x}, {y}) - attempting to delete point")
                    if self._view_model.delete_point_near(x, y, threshold=10.0):
                        return True
                else:
                    # LeftClick: Add point or start drag
                    log.d(f"LeftClick at ({x}, {y}) - adding point")
                    self._view_model.add_point(x, y)
                    self._is_dragging = False
                    self._drag_start_pos = (x, y)
                    return True
        
        elif event.type() == QMouseEvent.Type.MouseMove:
            if event.buttons() & Qt.MouseButton.LeftButton:
                if self._drag_start_pos is not None:
                    # Check if we've moved enough to consider it a drag
                    dx = x - self._drag_start_pos[0]
                    dy = y - self._drag_start_pos[1]
                    distance = (dx ** 2 + dy ** 2) ** 0.5
                    
                    if distance > 5.0:  # Threshold for drag detection
                        if not self._is_dragging:
                            self._is_dragging = True
                            log.d("Starting pan drag")
                        
                        # Pan the view
                        view_box = self._plot_widget.getViewBox()
                        current_range = view_box.viewRange()
                        x_range = current_range[0]
                        y_range = current_range[1]
                        
                        # Calculate pan delta
                        pan_dx = -dx * (x_range[1] - x_range[0]) / self._plot_widget.width()
                        pan_dy = dy * (y_range[1] - y_range[0]) / self._plot_widget.height()
                        
                        # Apply pan
                        view_box.setXRange(
                            x_range[0] + pan_dx,
                            x_range[1] + pan_dx,
                            padding=0
                        )
                        view_box.setYRange(
                            y_range[0] + pan_dy,
                            y_range[1] + pan_dy,
                            padding=0
                        )
                        
                        self._drag_start_pos = (x, y)
                        return True
        
        elif event.type() == QMouseEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                if self._is_dragging:
                    log.d("Ending pan drag")
                    self._is_dragging = False
                self._drag_start_pos = None
                return True
        
        return False

    def _handle_wheel_event(self, event: QWheelEvent) -> bool:
        """
        Handle wheel events for zooming.

        :param event: Wheel event
        :return: True if event was handled, False otherwise
        """
        modifiers = event.modifiers()
        
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Scroll: Zoom
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 0.9
            
            log.d(f"Ctrl+Scroll: zooming by factor {zoom_factor}")
            
            view_box = self._plot_widget.getViewBox()
            current_range = view_box.viewRange()
            x_range = current_range[0]
            y_range = current_range[1]
            
            # Get mouse position in scene coordinates
            pos = event.position()
            scene_pos = view_box.mapSceneToView(pos)
            center_x, center_y = scene_pos.x(), scene_pos.y()
            
            # Calculate new ranges centered on mouse position
            x_center = (x_range[0] + x_range[1]) / 2
            y_center = (y_range[0] + y_range[1]) / 2
            
            x_width = (x_range[1] - x_range[0]) * zoom_factor
            y_width = (y_range[1] - y_range[0]) * zoom_factor
            
            # Zoom towards mouse position
            x_offset = (center_x - x_center) * (1 - zoom_factor)
            y_offset = (center_y - y_center) * (1 - zoom_factor)
            
            new_x_range = [
                x_center - x_width / 2 + x_offset,
                x_center + x_width / 2 + x_offset
            ]
            new_y_range = [
                y_center - y_width / 2 + y_offset,
                y_center + y_width / 2 + y_offset
            ]
            
            view_box.setXRange(new_x_range[0], new_x_range[1], padding=0)
            view_box.setYRange(new_y_range[0], new_y_range[1], padding=0)
            
            return True
        
        return False

    def _handle_key_event(self, event: QKeyEvent) -> bool:
        """
        Handle key events for undo/redo.

        :param event: Key event
        :return: True if event was handled, False otherwise
        """
        if event.type() == QKeyEvent.Type.KeyPress:
            modifiers = event.modifiers()
            key = event.key()
            
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                if key == Qt.Key.Key_Z:
                    if modifiers & Qt.KeyboardModifier.ShiftModifier:
                        # Ctrl+Shift+Z: Redo
                        log.d("Ctrl+Shift+Z pressed - redo")
                        self._view_model.redo()
                        return True
                    else:
                        # Ctrl+Z: Undo
                        log.d("Ctrl+Z pressed - undo")
                        self._view_model.undo()
                        return True
        
        return False
