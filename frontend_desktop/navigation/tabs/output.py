import traceback
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from PySide6.QtCore import Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.muxer import VideoMuxer
from core.queue_manager import JobStatus, MuxJob, QueueCallback, QueueManager
from frontend_desktop.context import context
from frontend_desktop.global_signals import GSigs
from frontend_desktop.types.nav import Tabs
from frontend_desktop.widgets.scrollable_error_dialog import ScrollableErrorDialog

if TYPE_CHECKING:
    from frontend_desktop.main import MainWindow
    from frontend_desktop.navigation.tabs.audio import MultiAudioTab
    from frontend_desktop.navigation.tabs.chapters import ChapterTab
    from frontend_desktop.navigation.tabs.subtitles import MultiSubtitleTab
    from frontend_desktop.navigation.tabs.video import VideoTab


class MuxWorker(QThread):
    """Worker thread to process queue jobs - only runs when queue is active"""

    job_finished = Signal(UUID)
    job_failed = Signal(UUID, str)

    def __init__(self, queue_manager: QueueManager, parent=None) -> None:
        super().__init__(parent)
        self.queue_manager = queue_manager
        self.muxer = VideoMuxer()
        self.is_running = True

    def run(self) -> None:
        """Process jobs from queue sequentially"""
        while self.is_running:
            queued_jobs = self.queue_manager.get_queued_jobs()

            # if no jobs, exit the worker (queue is complete)
            if not queued_jobs:
                break

            job = queued_jobs[0]
            try:
                self.muxer.mux_from_job(job)
                self.job_finished.emit(job.job_id)
            except Exception as e:
                # catch any exceptions during muxing and link to the job
                error_msg = (
                    f"Muxing failed: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
                )
                self.job_failed.emit(job.job_id, error_msg)

    def stop(self) -> None:
        """Signal thread to stop gracefully after current job finishes"""
        self.is_running = False


class DesktopQueueCallback(QueueCallback):
    """Qt-specific callback that emits signals"""

    def __init__(self, parent: QWidget) -> None:
        super().__init__()
        self.parent = parent

    def on_job_added(self, job: MuxJob) -> None:
        pass

    def on_job_status_changed(self, job: MuxJob) -> None:
        pass

    def on_job_progress(self, job: MuxJob, progress: float, message: str) -> None:
        pass


class OutputTab(QWidget):
    """Tab for managing the muxing queue"""

    # internal signals for thread-safe UI updates
    _job_added_signal = Signal(MuxJob)
    _job_status_changed_signal = Signal(MuxJob)
    _job_progress_signal = Signal(UUID, float, str)

    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.setObjectName("OutputTab")

        self.main_window = parent

        # worker thread (only created when needed)
        self.worker: MuxWorker | None = None

        self.queue_manager = QueueManager()
        self.callback = DesktopQueueCallback(self)
        self.queue_manager.register_callback(self.callback)
        # track confirmation timers by job_id
        self.cancel_timers: dict[UUID, QTimer] = {}

        # listen for suggested output filepath generation
        GSigs().video_generate_output_filepath.connect(
            self._on_suggested_output_filepath
        )

        # connect internal signals
        self._job_added_signal.connect(self._on_job_added_ui)
        self._job_status_changed_signal.connect(self._on_job_status_changed_ui)
        self._job_progress_signal.connect(self._on_job_progress_ui)

        # override callback methods to emit signals
        self.callback.on_job_added = lambda job: self._job_added_signal.emit(job)
        self.callback.on_job_status_changed = (
            lambda job: self._job_status_changed_signal.emit(job)
        )
        self.callback.on_job_progress = (
            lambda job, progress, message: self._job_progress_signal.emit(
                job.job_id, progress, message
            )
        )

        # output path selection
        self.output_label = QLabel("Output File:", self)
        self.output_entry = QLineEdit(self, placeholderText="Select output file...")
        self.output_entry.setReadOnly(True)

        self.output_browse_btn = QPushButton("Browse", self)
        self.output_browse_btn.clicked.connect(self._browse_output_file)

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_entry, stretch=1)
        output_layout.addWidget(self.output_browse_btn)

        # queue table (removed "Created" column as suggested)
        self.queue_table = QTableWidget(0, 5, self)
        self.queue_table.setFrameShape(QFrame.Shape.Box)
        self.queue_table.setFrameShadow(QFrame.Shadow.Sunken)
        self.queue_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.queue_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.queue_table.setHorizontalHeaderLabels(
            ("Status", "Output File", "Progress", "Details", "Actions")
        )
        self.queue_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )

        # control buttons
        self.add_current_btn = QPushButton("Add Current to Queue", self)
        self.add_current_btn.clicked.connect(self._add_current_job)

        self.clear_completed_btn = QPushButton("Clear Completed", self)
        self.clear_completed_btn.clicked.connect(self._clear_completed)

        self.start_queue_btn = QPushButton("Start Queue", self)
        self.start_queue_btn.clicked.connect(self._start_queue)
        self.start_queue_btn.setCheckable(True)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_current_btn)
        btn_layout.addWidget(self.clear_completed_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_queue_btn)

        # stats and progress bar
        self.stats_label = QLabel("Queue: 0 jobs | 0 queued | 0 processing", self)
        self.progress_bar = QProgressBar(self, value=0, format="Completed: %v/%m (%p%)")

        stats_layout = QHBoxLayout()
        stats_layout.addWidget(self.stats_label)
        stats_layout.addWidget(self.progress_bar, stretch=1)

        # main_layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(output_layout)
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.queue_table, stretch=1)
        self.main_layout.addLayout(stats_layout)

        # initial refresh
        self._refresh_table()

    @Slot(object)
    def _on_suggested_output_filepath(self, suggested_path: Path) -> None:
        """Handle suggested output filepath from other tabs"""
        self.output_entry.setText(str(suggested_path))

    @Slot()
    def _browse_output_file(self) -> None:
        """Open file dialog to select output file"""
        # we'll prioritize the context last used path > output entry text > ""
        output_text = self.output_entry.text().strip()
        output_path = Path(output_text) if output_text else None
        browse_path = ""
        if context.last_used_path and output_path:
            browse_path = str(context.last_used_path / output_path.name)
        elif context.last_used_path:
            browse_path = str(context.last_used_path)
        elif output_path:
            browse_path = str(output_path)

        # open save file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output File",
            browse_path,
            "MP4 Files (*.mp4);;All Files (*)",
        )
        if file_path:
            self.output_entry.setText(file_path)

    @Slot()
    def _add_current_job(self) -> None:
        """Add current tab states to queue as a new job"""
        # check if output path exists and ask to overwrite if needed
        output_path = Path(self.output_entry.text().strip())
        if output_path.exists():
            if (
                QMessageBox.question(
                    self,
                    "Output File Exists",
                    f"{output_path}\n\npath already exists. Do you want to overwrite it?",
                )
                != QMessageBox.StandardButton.Yes
            ):
                GSigs().main_window_update_status_tip.emit(
                    "Output file already exists - please choose a different path", 3000
                )
                return

        # collect tab widgets from main window
        video_tab: VideoTab = self.main_window.tabs[Tabs.Video]
        audio_tabs: MultiAudioTab = self.main_window.tabs[Tabs.Audio]
        subtitle_tab: MultiSubtitleTab = self.main_window.tabs[Tabs.Subtitles]
        chapter_tab: ChapterTab = self.main_window.tabs[Tabs.Chapters]

        # validate output path
        output_path = self.output_entry.text().strip()
        if not output_path:
            GSigs().main_window_update_status_tip.emit(
                "Please select an output file", 3000
            )
            return

        # video
        # check if video tab is ready
        if not video_tab.is_tab_ready():
            GSigs().main_window_update_status_tip.emit(
                "Video tab is not ready - video file required", 3000
            )
            return

        # get video tab state
        video_state = video_tab.export_state()
        if not video_state:
            GSigs().main_window_update_status_tip.emit(
                "Cannot export video state", 3000
            )
            return

        # get audio states (optional - empty tabs are filtered out)
        audio_states = audio_tabs.export_all_audio_states()

        # get subtitle states (optional - empty tabs are filtered out)
        subtitle_states = subtitle_tab.export_all_subtitle_states()

        # gather chapters (optional)
        chapter_state = chapter_tab.export_state()

        # build MuxJob with full state objects
        job = MuxJob(
            video=video_state,
            audio_tracks=audio_states,
            subtitle_tracks=subtitle_states,
            chapters=chapter_state if chapter_state else None,
            output_file=Path(output_path),
        )

        # add to queue
        self.queue_manager.add_job(job)
        GSigs().main_window_update_status_tip.emit("Job added to queue", 2000)

        # reset all tabs after adding job
        video_tab.reset_tab()
        audio_tabs.multi_track.reset_to_single_tab()
        subtitle_tab.multi_track.reset_to_single_tab()
        chapter_tab.reset_tab()
        self.output_entry.clear()

    @Slot()
    def _clear_completed(self) -> None:
        """Remove completed/failed jobs from queue"""
        self.queue_manager.clear_completed()
        self._refresh_table()

    @Slot()
    def _start_queue(self) -> None:
        """Start/stop queue processing"""
        if self.start_queue_btn.isChecked():
            # only start if there are queued jobs
            if not self.queue_manager.get_queued_jobs():
                self.start_queue_btn.setChecked(False)
                return

            self.start_queue_btn.setText("Stop Queue")

            # create and start worker
            self.worker = MuxWorker(self.queue_manager, self)
            self.worker.job_finished.connect(self._on_job_finished)
            self.worker.job_failed.connect(self._on_job_failed)
            # thread naturally finishes
            self.worker.finished.connect(self._on_worker_finished)
            self.worker.start()
        else:
            self._stop_queue()

    def _stop_queue(self) -> None:
        """Stop queue processing"""
        self.start_queue_btn.setText("Start Queue")
        self.start_queue_btn.setChecked(False)

        if self.worker:
            self.worker.stop()
            # Wait for the worker thread to actually finish before clearing reference
            # this prevents threading errors during cleanup
            if self.worker.isRunning():
                self.worker.wait(2500)  # wait up to 2.5 seconds for graceful shutdown
            self.worker = None
            self._refresh_table()  # update UI after stopping

    @Slot(MuxJob)
    def _on_job_added_ui(self, _job: MuxJob) -> None:
        """Handle job added (thread-safe)"""
        self._refresh_table()

    @Slot(MuxJob)
    def _on_job_status_changed_ui(self, _job: MuxJob) -> None:
        """Handle job status change (thread-safe)"""
        self._refresh_table()

    @Slot(UUID, float, str)
    def _on_job_progress_ui(self, job_id: UUID, progress: float, _message: str) -> None:
        """Handle job progress update (thread-safe)"""
        for row in range(self.queue_table.rowCount()):
            item = self.queue_table.item(row, 0)
            if item:
                row_job_id = item.data(Qt.ItemDataRole.UserRole)
                if row_job_id == job_id:
                    progress_item = QTableWidgetItem(f"{progress:.1f}%")
                    self.queue_table.setItem(row, 2, progress_item)
                    break

    @Slot(UUID)
    def _on_job_finished(self, _job_id: UUID) -> None:
        """Handle individual job completion"""
        self._refresh_table()

    @Slot()
    def _on_worker_finished(self) -> None:
        """Handle worker thread finishing (no more jobs)"""
        # only stop if no more queued jobs (worker naturally exits when idle)
        if not self.queue_manager.get_queued_jobs():
            self._stop_queue()
        self._refresh_table()

    @Slot(UUID, str)
    def _on_job_failed(self, job_id: UUID, error_msg: str) -> None:
        """Handle job failure - store error message in job for display"""
        job = self.queue_manager.get_job(job_id)
        if job:
            job.error_message = error_msg
            self.queue_manager.update_job_status(job_id, JobStatus.FAILED)
        GSigs().main_window_update_status_tip.emit(
            f"Job failed: {error_msg[:75]}... (see details/logs)", 5000
        )
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Rebuild the entire table from queue state"""
        self.queue_table.setRowCount(0)

        jobs = self.queue_manager.get_all_jobs()
        for job in jobs:
            row = self.queue_table.rowCount()
            self.queue_table.insertRow(row)

            # status (with color coding)
            status_item = QTableWidgetItem(job.status.name)
            status_item.setData(Qt.ItemDataRole.UserRole, job.job_id)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # color code based on status
            if job.status == JobStatus.PROCESSING:
                status_item.setBackground(QColor(144, 238, 144))  # light green
            elif job.status == JobStatus.QUEUED:
                status_item.setBackground(QColor(255, 255, 153))  # light yellow
            elif job.status == JobStatus.CANCELLED:
                status_item.setBackground(QColor(255, 182, 193))  # light pink
            elif job.status == JobStatus.COMPLETED:
                status_item.setBackground(QColor(173, 216, 230))  # light blue
            elif job.status == JobStatus.FAILED:
                status_item.setBackground(QColor(255, 99, 71))  # tomato red

            self.queue_table.setItem(row, 0, status_item)

            # output file - show filename, tooltip shows full path with line breaks
            output_path = Path(job.output_file)
            output_item = QTableWidgetItem(output_path.name)
            output_item.setFlags(output_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # create formatted tooltip with line breaks every 60 characters
            full_path = str(job.output_file)
            tooltip_lines = []
            for i in range(0, len(full_path), 60):
                tooltip_lines.append(full_path[i : i + 60])
            output_item.setToolTip("\n".join(tooltip_lines))

            self.queue_table.setItem(row, 1, output_item)

            # progress
            progress_item = QTableWidgetItem(f"{job.progress:.1f}%")
            progress_item.setFlags(progress_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.queue_table.setItem(row, 2, progress_item)

            # details button - only for failed/cancelled jobs with error messages
            if (
                job.status in (JobStatus.FAILED, JobStatus.CANCELLED)
                and job.error_message
            ):
                details_btn = QPushButton("View Details", self)
                details_btn.clicked.connect(
                    lambda checked, jid=job.job_id: self._show_error_details(jid)
                )
                self.queue_table.setCellWidget(row, 3, details_btn)

            # actions (cancel button) - for queued or processing jobs
            if job.status in (JobStatus.QUEUED, JobStatus.PROCESSING):
                # determine button text based on whether confirmation is active
                button_text = (
                    "Confirm?" if job.job_id in self.cancel_timers else "Cancel"
                )
                cancel_btn = QPushButton(button_text, self)
                cancel_btn.clicked.connect(
                    lambda checked, jid=job.job_id: self._handle_cancel_click(jid)
                )
                self.queue_table.setCellWidget(row, 4, cancel_btn)

            # show remove button for completed/failed
            elif job.status in (
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            ):
                remove_btn = QPushButton("Remove", self)
                remove_btn.clicked.connect(
                    lambda checked, jid=job.job_id: self._remove_job(jid)
                )
                self.queue_table.setCellWidget(row, 4, remove_btn)

        # update stats
        total = len(jobs)
        queued = len([j for j in jobs if j.status == JobStatus.QUEUED])
        processing = len([j for j in jobs if j.status == JobStatus.PROCESSING])
        completed = len([j for j in jobs if j.status == JobStatus.COMPLETED])
        self.stats_label.setText(
            f"Queue: {total} jobs | {queued} queued | {processing} processing"
        )

        # update overall progress bar
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(completed)
        else:
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)

    def _cancel_job(self, job_id: UUID) -> None:
        """Cancel a specific job and kill process if running"""
        job = self.queue_manager.get_job(job_id)
        if not job:
            return

        # if job is processing, kill the active process
        if job.status == JobStatus.PROCESSING and self.worker:
            process = self.worker.muxer.active_processes.get(job_id)
            if process:
                self.worker.muxer._kill_process(process)

        self.queue_manager.cancel_job(job_id)
        self._refresh_table()

    def _handle_cancel_click(self, job_id: UUID) -> None:
        """Handle cancel button clicks with confirmation timer"""
        if job_id in self.cancel_timers:
            # second click within timeout - execute cancel
            timer = self.cancel_timers.pop(job_id)
            timer.stop()
            timer.deleteLater()
            self._cancel_job(job_id)
        else:
            # first click - start confirmation timer
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda jid=job_id: self._revert_cancel_timer(jid))
            timer.start(3000)
            self.cancel_timers[job_id] = timer
            self._refresh_table()  # refresh to show "Confirm?" text

    def _revert_cancel_timer(self, job_id: UUID) -> None:
        """Revert cancel button back to original state after timeout"""
        if job_id in self.cancel_timers:
            timer = self.cancel_timers.pop(job_id)
            timer.deleteLater()
            self._refresh_table()  # refresh to show "Cancel" text again

    def _remove_job(self, job_id: UUID) -> None:
        """Remove a completed/failed job"""
        self.queue_manager.remove_job(job_id)
        self._refresh_table()

    def _show_error_details(self, job_id: UUID) -> None:
        """Show error details in a scrollable dialog"""
        job = self.queue_manager.get_job(job_id)
        if not job or not job.error_message:
            return

        title = f"Job Error Details - {job.output_file.name}"
        dialog = ScrollableErrorDialog(
            error_message=job.error_message,
            title=title,
            parent_percentage=85,
            parent=self,
        )
        dialog.exec()

    def closeEvent(self, event) -> None:
        """Cleanup when tab is closed"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        self.queue_manager.unregister_callback(self.callback)
        super().closeEvent(event)
