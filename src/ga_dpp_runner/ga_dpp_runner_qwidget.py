"""Widget for GA DPP Runner UI."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.widgets.canvas_2d import (
    Canvas2DQWidget,
    Canvas2DQViewModel,
    Canvas2DInteractionHandler,
)
from src.core.widgets.canvas_2d.plot_data.plot_data_2d_enum import PlotData2D
from src.util.logger import Logger

from .ga_dpp_runner_qviewmodel import GaDPPRunnerQViewModel

log = Logger(__name__)


class LoadingOverlay(QWidget):
    """Overlay widget to show loading indicator."""

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the loading overlay.

        :param parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(0, 0, 0, 128);
            }
            QLabel {
                color: white;
                font-size: 16px;
                background-color: transparent;
            }
        """
        )

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label = QLabel("Loading...")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)
        self.setLayout(layout)

    def set_text(self, text: str):
        """Set the loading text.

        :param text: Text to display
        """
        self._label.setText(text)

    def show_overlay(self, parent_widget: QWidget):
        """Show the overlay on the parent widget.

        :param parent_widget: Parent widget to overlay
        """
        if parent_widget:
            self.setGeometry(parent_widget.rect())
            self.setParent(parent_widget)
            self.raise_()
            self.show()

    def hide_overlay(self):
        """Hide the overlay."""
        self.hide()


class GaDPPRunnerQWidget(QWidget):
    """Widget for GA DPP Runner UI."""

    def __init__(
        self,
        view_model: Optional[GaDPPRunnerQViewModel] = None,
        parent: Optional[QWidget] = None,
    ):
        """Initialize the GA DPP Runner widget.

        :param view_model: ViewModel instance. If None, creates a new one.
        :param parent: Parent widget
        """
        super().__init__(parent)
        self._view_model = view_model or GaDPPRunnerQViewModel()
        self._canvas_view_model = Canvas2DQViewModel()
        self._canvas_widget: Optional[Canvas2DQWidget] = None
        self._interaction_handler: Optional[Canvas2DInteractionHandler] = None

        # Drawing mode: "boundary" or "obstacle"
        self._drawing_mode = "boundary"
        self._current_boundary_id: Optional[str] = None
        self._current_obstacle_ids: list[str] = []

        # UI components
        self._branch_combo: Optional[QComboBox] = None
        self._refresh_branches_btn: Optional[QPushButton] = None
        self._flight_angle_spin: Optional[QDoubleSpinBox] = None
        self._boundary_margin_spin: Optional[QDoubleSpinBox] = None
        self._obstacle_margin_spin: Optional[QDoubleSpinBox] = None
        self._swath_spin: Optional[QDoubleSpinBox] = None
        self._start_point_spin: Optional[QSpinBox] = None
        self._perimeter_scaled_spin: Optional[QSpinBox] = None
        self._start_end_elongation_spin: Optional[QSpinBox] = None
        self._param_convention_spin: Optional[QSpinBox] = None
        self._execute_btn: Optional[QPushButton] = None
        self._status_label: Optional[QLabel] = None
        self._mode_combo: Optional[QComboBox] = None

        # Loading overlay
        self._loading_overlay = LoadingOverlay(self)

        self._setup_ui()
        self._connect_signals()

        # Load branches on initialization
        self._view_model.load_branches()

        log.d("Initialized GaDPPRunnerQWidget")

    def _setup_ui(self):
        """Set up the UI layout and components."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Top section: Branch selection
        branch_layout = QHBoxLayout()
        branch_label = QLabel("Branch:")
        self._branch_combo = QComboBox()
        self._branch_combo.setEditable(False)
        self._refresh_branches_btn = QPushButton("Refresh")
        branch_layout.addWidget(branch_label)
        branch_layout.addWidget(self._branch_combo)
        branch_layout.addWidget(self._refresh_branches_btn)
        branch_layout.addStretch()
        main_layout.addLayout(branch_layout)

        # Middle section: Split view (Canvas + Parameters)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Canvas
        canvas_container = QWidget()
        canvas_layout = QVBoxLayout()
        canvas_layout.setContentsMargins(0, 0, 0, 0)

        # Canvas mode selector
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Drawing Mode:")
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Boundary", "Obstacle"])
        self._mode_combo.setCurrentText("Boundary")
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self._mode_combo)
        mode_layout.addStretch()
        canvas_layout.addLayout(mode_layout)

        # Canvas widget
        self._canvas_widget = Canvas2DQWidget(self._canvas_view_model, self)
        self._interaction_handler = Canvas2DInteractionHandler(
            self._canvas_view_model, self._canvas_widget.plot_widget
        )
        canvas_layout.addWidget(self._canvas_widget)
        canvas_container.setLayout(canvas_layout)
        splitter.addWidget(canvas_container)

        # Right: Parameter inputs
        params_group = QGroupBox("Parameters")
        params_layout = QFormLayout()

        self._flight_angle_spin = QDoubleSpinBox()
        self._flight_angle_spin.setRange(-180.0, 180.0)
        self._flight_angle_spin.setValue(0.0)
        self._flight_angle_spin.setDecimals(2)
        params_layout.addRow("Flight Angle (degrees):", self._flight_angle_spin)

        self._boundary_margin_spin = QDoubleSpinBox()
        self._boundary_margin_spin.setRange(0.0, 100.0)
        self._boundary_margin_spin.setValue(2.5)
        self._boundary_margin_spin.setDecimals(2)
        params_layout.addRow("Boundary Margin:", self._boundary_margin_spin)

        self._obstacle_margin_spin = QDoubleSpinBox()
        self._obstacle_margin_spin.setRange(0.0, 100.0)
        self._obstacle_margin_spin.setValue(2.0)
        self._obstacle_margin_spin.setDecimals(2)
        params_layout.addRow("Obstacle Margin:", self._obstacle_margin_spin)

        self._swath_spin = QDoubleSpinBox()
        self._swath_spin.setRange(0.1, 100.0)
        self._swath_spin.setValue(4.0)
        self._swath_spin.setDecimals(2)
        params_layout.addRow("Swath:", self._swath_spin)

        self._start_point_spin = QSpinBox()
        self._start_point_spin.setRange(1, 4)
        self._start_point_spin.setValue(1)
        params_layout.addRow("Start Point:", self._start_point_spin)

        self._perimeter_scaled_spin = QSpinBox()
        self._perimeter_scaled_spin.setRange(0, 10)
        self._perimeter_scaled_spin.setValue(1)
        params_layout.addRow("Perimeter Scaled No:", self._perimeter_scaled_spin)

        self._start_end_elongation_spin = QSpinBox()
        self._start_end_elongation_spin.setRange(0, 1)
        self._start_end_elongation_spin.setValue(1)
        params_layout.addRow("Start/End Elongation Flag:", self._start_end_elongation_spin)

        self._param_convention_spin = QSpinBox()
        self._param_convention_spin.setRange(0, 1)
        self._param_convention_spin.setValue(0)
        params_layout.addRow("Param Convention:", self._param_convention_spin)

        params_group.setLayout(params_layout)
        splitter.addWidget(params_group)

        # Set splitter proportions (60% canvas, 40% params)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter, stretch=1)

        # Bottom section: Execute button and status
        bottom_layout = QHBoxLayout()
        self._execute_btn = QPushButton("Execute Algorithm")
        self._status_label = QLabel("Ready")
        bottom_layout.addWidget(self._execute_btn)
        bottom_layout.addWidget(self._status_label)
        bottom_layout.addStretch()
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def _connect_signals(self):
        """Connect signals and slots."""
        # Branch management
        self._branch_combo.currentTextChanged.connect(self._on_branch_changed)
        self._refresh_branches_btn.clicked.connect(self._view_model.load_branches)

        # View model signals
        self._view_model.branches_loaded.connect(self._on_branches_loaded)
        self._view_model.branch_changed.connect(self._on_branch_changed_success)
        self._view_model.loading_changed.connect(self._on_loading_changed)
        self._view_model.execution_started.connect(self._on_execution_started)
        self._view_model.execution_completed.connect(self._on_execution_completed)
        self._view_model.execution_error.connect(self._on_execution_error)

        # Drawing mode
        self._mode_combo.currentTextChanged.connect(self._on_drawing_mode_changed)

        # Execute button
        self._execute_btn.clicked.connect(self._on_execute_clicked)

    def _on_branches_loaded(self, branches: list[str]):
        """Handle branches loaded signal.

        :param branches: List of branch names
        """
        log.d(f"Branches loaded: {len(branches)}")
        current_branch = self._branch_combo.currentText()
        self._branch_combo.clear()
        self._branch_combo.addItems(branches)
        # Try to restore previous selection
        if current_branch and current_branch in branches:
            self._branch_combo.setCurrentText(current_branch)

    def _on_branch_changed(self, branch_name: str):
        """Handle branch selection change.

        :param branch_name: Selected branch name
        """
        if branch_name:
            log.d(f"Branch changed to: {branch_name}")
            self._view_model.change_branch(branch_name)

    def _on_branch_changed_success(self, branch_name: str):
        """Handle successful branch change.

        :param branch_name: Branch name that was checked out
        """
        log.d(f"Successfully changed to branch: {branch_name}")
        self._status_label.setText(f"Switched to branch: {branch_name}")

    def _on_loading_changed(self, loading: bool):
        """Handle loading state change.

        :param loading: Whether loading is active
        """
        if loading:
            self._loading_overlay.show_overlay(self)
            self._execute_btn.setEnabled(False)
            self._branch_combo.setEnabled(False)
            self._refresh_branches_btn.setEnabled(False)
        else:
            self._loading_overlay.hide_overlay()
            self._execute_btn.setEnabled(True)
            self._branch_combo.setEnabled(True)
            self._refresh_branches_btn.setEnabled(True)

    def _on_execution_started(self):
        """Handle execution started signal."""
        log.d("Execution started")
        self._status_label.setText("Executing algorithm...")
        self._loading_overlay.set_text("Executing algorithm...")

    def _on_execution_completed(self, output: str):
        """Handle execution completed signal.

        :param output: Output from execution
        """
        log.d("Execution completed")
        self._status_label.setText("Execution completed successfully")
        # Show output in message box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Execution Result")
        msg_box.setText("Algorithm execution completed successfully.")
        msg_box.setDetailedText(output)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def _on_execution_error(self, error_msg: str):
        """Handle execution error signal.

        :param error_msg: Error message
        """
        log.e(f"Execution error: {error_msg}")
        self._status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "Execution Error", f"An error occurred:\n\n{error_msg}")

    def _on_drawing_mode_changed(self, mode: str):
        """Handle drawing mode change.

        :param mode: Drawing mode ("Boundary" or "Obstacle")
        """
        log.d(f"Drawing mode changed to: {mode}")
        self._drawing_mode = mode.lower()
        # Clear current plot to allow starting new one
        self._canvas_view_model.clear_current_plot()
        # Set plot type to polygon for both boundary and obstacle
        self._canvas_view_model.current_plot_type = PlotData2D.POLYGON
        # Note: Colors are set in the view model (green for polygon by default)
        # We could customize colors here if needed

    def _on_execute_clicked(self):
        """Handle execute button click."""
        log.d("Execute button clicked")

        # Extract boundary and obstacles from canvas
        boundary_list = self._extract_boundary()
        obstacle_list = self._extract_obstacles()

        if not boundary_list:
            QMessageBox.warning(
                self, "Missing Input", "Please draw a boundary on the canvas."
            )
            return

        # Collect parameters
        # obstacle_margin should be a list with one margin per obstacle
        obstacle_margin_value = self._obstacle_margin_spin.value()
        obstacle_margin = (
            [obstacle_margin_value] * len(obstacle_list)
            if obstacle_list
            else []
        )

        params = {
            "boundary_list": boundary_list,
            "flight_angle_degrees": self._flight_angle_spin.value(),
            "boundary_margin": self._boundary_margin_spin.value(),
            "obstacle_margin": obstacle_margin,
            "swath": self._swath_spin.value(),
            "obstacle_list": obstacle_list if obstacle_list else None,
            "start_point": self._start_point_spin.value(),
            "perimter_scaled_no": self._perimeter_scaled_spin.value(),
            "start_end_elongation_flag": self._start_end_elongation_spin.value(),
            "param_convention": self._param_convention_spin.value(),
        }

        log.d(f"Executing with params: {params}")
        self._view_model.execute_algorithm(params)

    def _extract_boundary(self) -> list[list[float]]:
        """Extract boundary coordinates from canvas.

        :return: List of [x, y] coordinate pairs
        """
        boundary_list = []
        plot_data = self._canvas_view_model.plot_data

        # Find boundary polygon (we'll use the first polygon as boundary for now)
        # In a more sophisticated implementation, we could tag polygons
        for plot in plot_data.get_all_plots():
            if plot.type == PlotData2D.POLYGON:
                # For now, use the first polygon as boundary
                # In a real implementation, we'd track which is boundary vs obstacle
                points = plot.points
                if len(points) >= 3:
                    boundary_list = [[point.x, point.y] for point in points]
                    # Remove closing point if present
                    if boundary_list and boundary_list[0] == boundary_list[-1]:
                        boundary_list = boundary_list[:-1]
                    break

        return boundary_list

    def _extract_obstacles(self) -> Optional[list[list[list[float]]]]:
        """Extract obstacle coordinates from canvas.

        :return: List of obstacles, where each obstacle is a list of [x, y] coordinate pairs
        """
        obstacles = []
        plot_data = self._canvas_view_model.plot_data

        # Find all polygons (we'll use all polygons except the first one as obstacles)
        # In a more sophisticated implementation, we could tag polygons
        polygons = [
            plot
            for plot in plot_data.get_all_plots()
            if plot.type == PlotData2D.POLYGON
        ]

        if len(polygons) > 1:
            # Skip first polygon (boundary), use rest as obstacles
            for plot in polygons[1:]:
                points = plot.points
                if len(points) >= 3:
                    obstacle_points = [[point.x, point.y] for point in points]
                    # Remove closing point if present
                    if obstacle_points and obstacle_points[0] == obstacle_points[-1]:
                        obstacle_points = obstacle_points[:-1]
                    if obstacle_points:
                        obstacles.append(obstacle_points)

        return obstacles if obstacles else None

    @property
    def view_model(self) -> GaDPPRunnerQViewModel:
        """Get the view model."""
        return self._view_model

    @property
    def canvas_widget(self) -> Canvas2DQWidget:
        """Get the canvas widget."""
        return self._canvas_widget
