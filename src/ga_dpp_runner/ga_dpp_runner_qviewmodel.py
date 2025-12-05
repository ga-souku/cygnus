"""ViewModel for GA DPP Runner widget."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal

from src.util.logger import Logger

log = Logger(__name__)


class GitBranchLoaderThread(QThread):
    """Thread for loading git branches asynchronously."""

    branches_loaded = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, repo_path: Path):
        """Initialize the branch loader thread.

        :param repo_path: Path to the git repository
        """
        super().__init__()
        self._repo_path = repo_path

    def run(self):
        """Run the branch loading process."""
        try:
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=str(self._repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
            branches = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Remove current branch marker
                if line.startswith("*"):
                    line = line[1:].strip()
                # Remove remote prefix (e.g., "remotes/origin/")
                if "/" in line:
                    # Take the last part after the last /
                    line = line.split("/")[-1]
                # Skip HEAD references
                if "HEAD" in line:
                    continue
                if line and line not in branches:
                    branches.append(line)
            branches.sort()
            self.branches_loaded.emit(branches)
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to load branches: {e.stderr}"
            log.e(error_msg)
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error loading branches: {str(e)}"
            log.e(error_msg)
            self.error_occurred.emit(error_msg)


class GitBranchChangerThread(QThread):
    """Thread for changing git branch asynchronously."""

    branch_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, repo_path: Path, branch_name: str):
        """Initialize the branch changer thread.

        :param repo_path: Path to the git repository
        :param branch_name: Name of the branch to checkout
        """
        super().__init__()
        self._repo_path = repo_path
        self._branch_name = branch_name

    def run(self):
        """Run the branch change process."""
        try:
            result = subprocess.run(
                ["git", "checkout", self._branch_name],
                cwd=str(self._repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
            self.branch_changed.emit(self._branch_name)
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to change branch: {e.stderr}"
            log.e(error_msg)
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error changing branch: {str(e)}"
            log.e(error_msg)
            self.error_occurred.emit(error_msg)


class ScriptExecutorThread(QThread):
    """Thread for executing Python script asynchronously."""

    execution_completed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, script_path: Path, working_dir: Path):
        """Initialize the script executor thread.

        :param script_path: Path to the Python script to execute
        :param working_dir: Working directory for script execution
        """
        super().__init__()
        self._script_path = script_path
        self._working_dir = working_dir

    def run(self):
        """Run the script execution process."""
        try:
            result = subprocess.run(
                ["python", str(self._script_path)],
                cwd=str(self._working_dir),
                capture_output=True,
                text=True,
                check=True,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nStderr: {result.stderr}"
            self.execution_completed.emit(output)
        except subprocess.CalledProcessError as e:
            error_msg = f"Script execution failed: {e.stderr or str(e)}"
            log.e(error_msg)
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error executing script: {str(e)}"
            log.e(error_msg)
            self.error_occurred.emit(error_msg)


class GaDPPRunnerQViewModel(QObject):
    """ViewModel for managing GA DPP Runner business logic."""

    # Signals
    loading_changed = Signal(bool)  # Emitted when loading state changes
    branches_loaded = Signal(list)  # Emitted with list of branch names
    branch_changed = Signal(str)  # Emitted when branch change completes
    execution_started = Signal()  # Emitted when execution starts
    execution_completed = Signal(str)  # Emitted with output when execution completes
    execution_error = Signal(str)  # Emitted with error message on failure

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the view model.

        :param project_root: Root path of the project. If None, will be inferred.
        """
        super().__init__()
        if project_root is None:
            # Try to infer project root from current file location
            current_file = Path(__file__).resolve()
            # Go up from src/ga_dpp_runner/ to project root
            project_root = current_file.parent.parent.parent
        self._project_root = Path(project_root)
        self._ga_dpp1_path = self._project_root / "ga_dpp1"
        self._dppv2_path = self._ga_dpp1_path / "dppv2"

        # Threads for async operations
        self._branch_loader_thread: Optional[GitBranchLoaderThread] = None
        self._branch_changer_thread: Optional[GitBranchChangerThread] = None
        self._script_executor_thread: Optional[ScriptExecutorThread] = None

        log.d(f"Initialized GaDPPRunnerQViewModel with project root: {self._project_root}")

    def load_branches(self):
        """Load all branches from the ga_dpp1 repository."""
        if self._branch_loader_thread and self._branch_loader_thread.isRunning():
            log.w("Branch loader thread already running")
            return

        log.d("Loading branches from ga_dpp1 repository")
        self.loading_changed.emit(True)

        self._branch_loader_thread = GitBranchLoaderThread(self._ga_dpp1_path)
        self._branch_loader_thread.branches_loaded.connect(self._on_branches_loaded)
        self._branch_loader_thread.error_occurred.connect(self._on_branch_loader_error)
        self._branch_loader_thread.finished.connect(
            lambda: self.loading_changed.emit(False)
        )
        self._branch_loader_thread.start()

    def _on_branches_loaded(self, branches: list[str]):
        """Handle branches loaded signal.

        :param branches: List of branch names
        """
        log.d(f"Loaded {len(branches)} branches")
        self.branches_loaded.emit(branches)

    def _on_branch_loader_error(self, error_msg: str):
        """Handle branch loader error.

        :param error_msg: Error message
        """
        log.e(f"Branch loader error: {error_msg}")
        self.execution_error.emit(error_msg)

    def change_branch(self, branch_name: str):
        """Change the git branch of the ga_dpp1 repository.

        :param branch_name: Name of the branch to checkout
        """
        if self._branch_changer_thread and self._branch_changer_thread.isRunning():
            log.w("Branch changer thread already running")
            return

        log.d(f"Changing branch to: {branch_name}")
        self.loading_changed.emit(True)

        self._branch_changer_thread = GitBranchChangerThread(
            self._ga_dpp1_path, branch_name
        )
        self._branch_changer_thread.branch_changed.connect(self._on_branch_changed)
        self._branch_changer_thread.error_occurred.connect(self._on_branch_changer_error)
        self._branch_changer_thread.finished.connect(
            lambda: self.loading_changed.emit(False)
        )
        self._branch_changer_thread.start()

    def _on_branch_changed(self, branch_name: str):
        """Handle branch changed signal.

        :param branch_name: Name of the branch that was checked out
        """
        log.d(f"Successfully changed to branch: {branch_name}")
        self.branch_changed.emit(branch_name)

    def _on_branch_changer_error(self, error_msg: str):
        """Handle branch changer error.

        :param error_msg: Error message
        """
        log.e(f"Branch changer error: {error_msg}")
        self.execution_error.emit(error_msg)

    def execute_algorithm(self, params: dict):
        """Execute the algorithm with the given parameters.

        :param params: Dictionary containing algorithm parameters
        """
        if self._script_executor_thread and self._script_executor_thread.isRunning():
            log.w("Script executor thread already running")
            return

        log.d("Executing algorithm with parameters")
        self.loading_changed.emit(True)
        self.execution_started.emit()

        # Create execution script
        script_path = self._create_execution_script(params)
        if script_path is None:
            error_msg = "Failed to create execution script"
            log.e(error_msg)
            self.execution_error.emit(error_msg)
            self.loading_changed.emit(False)
            return

        # Execute script in thread
        self._script_executor_thread = ScriptExecutorThread(
            script_path, self._dppv2_path
        )
        self._script_executor_thread.execution_completed.connect(
            self._on_execution_completed
        )
        self._script_executor_thread.error_occurred.connect(
            self._on_script_executor_error
        )
        self._script_executor_thread.finished.connect(
            lambda: self.loading_changed.emit(False)
        )
        self._script_executor_thread.start()

    def _create_execution_script(self, params: dict) -> Optional[Path]:
        """Create a Python script that executes the algorithm.

        :param params: Dictionary containing algorithm parameters
        :return: Path to the created script, or None if creation failed
        """
        try:
            # Extract parameters (skip area_threshold and settings as specified)
            boundary_list = params.get("boundary_list", [])
            flight_angle_degrees = params.get("flight_angle_degrees")
            boundary_margin = params.get("boundary_margin")
            obstacle_margin = params.get("obstacle_margin")
            swath = params.get("swath")
            obstacle_list = params.get("obstacle_list")
            start_point = params.get("start_point", 1)
            perimter_scaled_no = params.get("perimter_scaled_no", 1)
            start_end_elongation_flag = params.get("start_end_elongation_flag", 1)
            param_convention = params.get("param_convention", 0)

            # Create temporary script file
            script_content = f'''"""Temporary script to execute DPP algorithm."""

import json
import sys
from dppv2.main import execute

# Parameters
boundary_list = {json.dumps(boundary_list)}
flight_angle_degrees = {json.dumps(flight_angle_degrees)}
boundary_margin = {json.dumps(boundary_margin)}
obstacle_margin = {json.dumps(obstacle_margin)}
swath = {json.dumps(swath)}
obstacle_list = {json.dumps(obstacle_list)}
start_point = {json.dumps(start_point)}
perimter_scaled_no = {json.dumps(perimter_scaled_no)}
start_end_elongation_flag = {json.dumps(start_end_elongation_flag)}
param_convention = {json.dumps(param_convention)}

try:
    # Execute the algorithm
    dpp_out = execute(
        boundary_list=boundary_list,
        flight_angle_degrees=flight_angle_degrees,
        boundary_margin=boundary_margin,
        obstacle_margin=obstacle_margin,
        swath=swath,
        area_threshold=None,  # Skipped as specified
        obstacle_list=obstacle_list,
        start_point=start_point,
        perimter_scaled_no=perimter_scaled_no,
        start_end_elongation_flag=start_end_elongation_flag,
        param_convention=param_convention,
        settings=None  # Skipped as specified
    )
    
    # Serialize output to JSON
    output = {{
        "result_1": dpp_out.result_1 if hasattr(dpp_out, 'result_1') else None,
        "result_2": dpp_out.result_2 if hasattr(dpp_out, 'result_2') else None,
        "result_3": dpp_out.result_3 if hasattr(dpp_out, 'result_3') else None,
        "result_4": dpp_out.result_4 if hasattr(dpp_out, 'result_4') else None,
        "coverage_area_acres": dpp_out.coverage_area_acres if hasattr(dpp_out, 'coverage_area_acres') else None,
        "field_area": dpp_out.field_area if hasattr(dpp_out, 'field_area') else None,
        "obstacles_area": dpp_out.obstacles_area if hasattr(dpp_out, 'obstacles_area') else None,
        "flight_angle_degrees": dpp_out.flight_angle_degrees if hasattr(dpp_out, 'flight_angle_degrees') else None,
    }}
    
    print(json.dumps(output, indent=2))
    print("\\nExecution completed successfully", file=sys.stderr)
    
except Exception as e:
    print(f"Error: {{str(e)}}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''

            # Create script file in dppv2 directory
            script_path = self._dppv2_path / f"run_dpp_{os.getpid()}_{id(self)}.py"
            script_path.write_text(script_content, encoding="utf-8")
            log.d(f"Created execution script: {script_path}")

            return script_path

        except Exception as e:
            log.e(f"Failed to create execution script: {str(e)}")
            return None

    def _on_execution_completed(self, output: str):
        """Handle execution completed signal.

        :param output: Output from the script execution
        """
        log.d("Algorithm execution completed successfully")
        self.execution_completed.emit(output)

    def _on_script_executor_error(self, error_msg: str):
        """Handle script executor error.

        :param error_msg: Error message
        """
        log.e(f"Script executor error: {error_msg}")
        self.execution_error.emit(error_msg)

    @property
    def project_root(self) -> Path:
        """Get the project root path."""
        return self._project_root

    @property
    def ga_dpp1_path(self) -> Path:
        """Get the ga_dpp1 repository path."""
        return self._ga_dpp1_path

    @property
    def dppv2_path(self) -> Path:
        """Get the dppv2 directory path."""
        return self._dppv2_path
