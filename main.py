"""Demo application for 2D Canvas system."""

import sys

from PySide6.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from src.core.widgets.canvas_2d import Canvas2DQWidget, Canvas2DQViewModel, Canvas2DInteractionHandler
from src.core.widgets.canvas_2d.plot_data.plot_data_2d_enum import PlotData2D
from src.util.logger import Logger

log = Logger(__name__)

class MainWindow(QMainWindow):
    """Main window for the demo application."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        log.d("Initializing main window")
        
        # Set window properties
        self.setWindowTitle("2D Canvas Demo - PyQtGraph")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create control panel
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Create view model
        log.d("Creating Canvas2DQViewModel")
        self._view_model = Canvas2DQViewModel()
        
        # Create canvas widget
        log.d("Creating Canvas2DQWidget")
        self._canvas_widget = Canvas2DQWidget(self._view_model)
        main_layout.addWidget(self._canvas_widget)
        
        # Create interaction handler
        log.d("Creating Canvas2DInteractionHandler")
        self._interaction_handler = Canvas2DInteractionHandler(
            self._view_model,
            self._canvas_widget.plot_widget
        )
        
        # Connect dropdown to view model
        self._plot_type_combo.currentTextChanged.connect(self._on_plot_type_changed)
        
        # Set initial plot type
        self._on_plot_type_changed("Point")
        
        log.d("Main window initialization complete")

    def _create_control_panel(self) -> QWidget:
        """
        Create the control panel with dropdown menu.

        :return: Control panel widget
        """
        log.d("Creating control panel")
        
        panel = QWidget()
        layout = QHBoxLayout()
        panel.setLayout(layout)
        
        # Label for dropdown
        label = QLabel("Plot Type:")
        layout.addWidget(label)
        
        # Dropdown menu for plot type selection
        self._plot_type_combo = QComboBox()
        self._plot_type_combo.addItems(["Point", "Polyline", "Polygon"])
        self._plot_type_combo.setCurrentText("Point")
        layout.addWidget(self._plot_type_combo)
        
        # Add stretch to push controls to the left
        layout.addStretch()
        
        # Instructions label
        instructions = QLabel(
            "Instructions: LeftClick=Add Point | Ctrl+LeftClick=Delete Point | "
            "Ctrl+Scroll=Zoom | Ctrl+Z=Undo | Ctrl+Shift+Z=Redo | LeftClick+Drag=Pan"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        log.d("Control panel created")
        return panel

    def _on_plot_type_changed(self, text: str):
        """
        Handle plot type selection change.

        :param text: Selected plot type text
        """
        log.d(f"Plot type changed to: {text}")
        
        # Map text to enum
        plot_type_map = {
            "Point": PlotData2D.POINT,
            "Polyline": PlotData2D.POLYLINE,
            "Polygon": PlotData2D.POLYGON,
        }
        
        if text in plot_type_map:
            plot_type = plot_type_map[text]
            self._view_model.current_plot_type = plot_type
            self._view_model.clear_current_plot()
            log.d(f"Set plot type to {plot_type.value}")
        else:
            log.w(f"Unknown plot type: {text}")


def main():
    """Main entry point for the demo application."""
    log.d("Starting 2D Canvas Demo Application")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("2D Canvas Demo")
    
    log.d("QApplication created")
    
    # Create and show main window
    log.d("Creating main window")
    window = MainWindow()
    window.show()
    
    log.d("Main window shown, entering event loop")
    
    # Run event loop
    exit_code = app.exec()
    
    log.d(f"Application exiting with code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
