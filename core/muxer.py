import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from uuid import UUID

import psutil

from core.logger import LOG
from core.queue_manager import JobStatus, MuxJob, QueueManager


class ProgressCallback:
    """Override this in the UI layer"""

    def on_progress(self, percent: float, message: str) -> None:
        pass

    def on_complete(self, output_file: str) -> None:
        pass

    def on_error(self, error: str) -> None:
        pass


class VideoMuxer:
    """Pure business logic - works with ANY frontend"""

    def __init__(self, progress_callback: Optional[ProgressCallback] = None) -> None:
        self.progress_callback = progress_callback
        self.queue_manager = QueueManager()
        # track processes by job_id
        self.active_processes: dict[UUID, subprocess.Popen] = {}

    def mux_from_job(self, job: MuxJob) -> None:
        """Process a MuxJob from the queue"""
        # self._mock_mux_with_ping(job)
        LOG.debug(f"Mux job: {job}")
        self._mux_with_mp4box(job)

    def _mock_mux_with_ping(self, job: MuxJob):
        """Mock processing with ping for testing GUI controls"""
        process = None
        try:
            self.queue_manager.update_job_status(job.job_id, JobStatus.PROCESSING)

            # Check if job was cancelled before starting
            current_job = self.queue_manager.get_job(job.job_id)
            if current_job and current_job.status == JobStatus.CANCELLED:
                return

            # Mock processing with ping (50 pings)
            # On Windows: ping -n 50 127.0.0.1
            # On Unix: ping -c 50 127.0.0.1
            is_windows = platform.system() == "Windows"
            if is_windows:
                cmd = ["ping", "-n", "20", "127.0.0.1"]
            else:
                cmd = ["ping", "-c", "20", "127.0.0.1"]

            # Create subprocess with no window on Windows
            startupinfo = None
            if is_windows:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if is_windows else 0,
            )

            # Store process for potential cancellation
            self.active_processes[job.job_id] = process

            # Parse ping output for progress
            ping_count = 0
            total_pings = 20

            assert process.stdout is not None  # Created with stdout=PIPE
            for line in process.stdout:
                # Check if job was cancelled
                current_job = self.queue_manager.get_job(job.job_id)
                if current_job and current_job.status == JobStatus.CANCELLED:
                    self._kill_process(process)
                    return

                # Count successful pings (look for "Reply from" or "bytes from")
                if "reply from" in line.lower() or "bytes from" in line.lower():
                    ping_count += 1
                    percent = (ping_count / total_pings) * 100
                    message = f"Processing ping {ping_count}/{total_pings}"

                    self._notify_progress(percent, message)
                    self.queue_manager.update_job_progress(job.job_id, percent, message)

            # Wait for process to complete
            return_code = process.wait()

            # Clean up process tracking
            self.active_processes.pop(job.job_id, None)

            # Check final status
            current_job = self.queue_manager.get_job(job.job_id)
            if current_job and current_job.status == JobStatus.CANCELLED:
                return

            if return_code == 0:
                self.queue_manager.update_job_status(job.job_id, JobStatus.COMPLETED)
                self._notify_complete(str(job.output_file))
            else:
                stderr = process.stderr.read() if process.stderr else "Unknown error"
                self.queue_manager.update_job_status(
                    job.job_id, JobStatus.FAILED, stderr
                )
                self._notify_error(stderr)

        except Exception as e:
            error_msg = str(e)
            self.queue_manager.update_job_status(
                job.job_id, JobStatus.FAILED, error_msg
            )
            self._notify_error(error_msg)
        finally:
            # Clean up process if still running
            if process and process.poll() is None:
                self._kill_process(process)
            self.active_processes.pop(job.job_id, None)

    def _mux_with_mp4box(self, job: MuxJob) -> None:
        """MP4Box muxing implementation."""
        process = None

        try:
            self.queue_manager.update_job_status(job.job_id, JobStatus.PROCESSING)

            # check if job was cancelled before starting
            current_job = self.queue_manager.get_job(job.job_id)
            if current_job and current_job.status == JobStatus.CANCELLED:
                return

            # build MP4Box command
            cmd = ["mp4box"]

            # add video track
            if job.video:
                video_opts = "#video"
                if job.video.language:
                    video_opts += f":lang={job.video.language.part3}"
                video_opts += (
                    f":name={job.video.title}" if job.video.title else ":name="
                )
                video_opts += (
                    f":delay={job.video.delay_ms}"
                    if job.video.delay_ms != 0
                    else ":delay="
                )
                cmd.extend(["-add", f"{job.video.input_file}{video_opts}"])

            # add audio tracks
            audio_defaults_set = any(audio.default for audio in job.audio_tracks)
            for audio in job.audio_tracks:
                # use specific track_id if provided (for multi-track MP4), otherwise use #audio
                if audio.track_id is not None:
                    audio_opts = f"#{audio.track_id}"
                else:
                    audio_opts = "#audio"

                if audio.language:
                    audio_opts += f":lang={audio.language.part3}"
                audio_opts += f":name={audio.title}" if audio.title else ":name="
                if audio.delay_ms != 0:
                    audio_opts += f":delay={audio.delay_ms}"

                # default flag logic
                if audio.default:
                    audio_opts += ":tkhd=3:group=1"
                elif audio_defaults_set:
                    # explicitly disable default if another track is default
                    audio_opts += ":tkhd=0:group=1"

                cmd.extend(["-add", f"{audio.input_file}{audio_opts}"])

            # add subtitle tracks with default/forced logic
            subtitle_defaults_set = any(sub.default for sub in job.subtitle_tracks)
            for subtitle in job.subtitle_tracks:
                # determine track selector (for multi-track MP4 inputs)
                if subtitle.track_id is not None:
                    track_selector = f"#{subtitle.track_id}"
                else:
                    track_selector = "#text"  # default to first text track

                subtitle_opts = track_selector
                if subtitle.language:
                    subtitle_opts += f":lang={subtitle.language.part3}"
                subtitle_opts += (
                    f":name={subtitle.title}" if subtitle.title else ":name="
                )

                # default flag logic
                if subtitle.default:
                    subtitle_opts += ":tkhd=3:group=2"
                elif subtitle_defaults_set:
                    # explicitly disable default if another track is default
                    subtitle_opts += ":tkhd=0:group=2"

                # forced flag
                if subtitle.forced:
                    subtitle_opts += ":txtflags=0xC0000000"

                cmd.extend(["-add", f"{subtitle.input_file}{subtitle_opts}"])

            # add chapters if present
            chapters_path: Path | None = None
            if job.chapters and job.chapters.chapters:
                temp_file = tempfile.NamedTemporaryFile(
                    prefix="mp4bc_", suffix=".txt", delete=False
                )
                temp_file.write(job.chapters.chapters.encode("utf-8"))
                temp_file.close()  # we must close before MP4Box can read it (Windows file locking)
                chapters_path = Path(temp_file.name)
                cmd.extend(["-chap", str(chapters_path)])

            # -hdr none: prevents MP4Box adding double metadata headers
            # -proglf: enable progress logging for parsing
            # -new: create new output file
            cmd.extend(["-hdr", "none", "-proglf", "-new", str(job.output_file)])
            LOG.debug(f"MP4Box command: {' '.join(cmd)}")

            # create subprocess with no window on Windows
            startupinfo = None
            creationflags = 0
            is_windows = platform.system() == "Windows"
            if is_windows:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )

            self.active_processes[job.job_id] = process

            # Calculate total operations for accurate progress tracking
            # MP4Box processes: video + audio track(s) + subtitle track(s) + final write
            total_operations = 1  # video track (always present)
            total_operations += len(job.audio_tracks)
            total_operations += len(job.subtitle_tracks)
            total_operations += 1  # final ISO file writing

            current_operation = 0
            last_operation_progress = 0
            all_output = []

            if not process.stdout:
                raise RuntimeError("Failed to capture MP4Box output")

            for line in process.stdout:
                # check if job was cancelled
                current_job = self.queue_manager.get_job(job.job_id)
                if current_job and current_job.status == JobStatus.CANCELLED:
                    self._kill_process(process)
                    return

                line = line.strip()
                if line:
                    LOG.debug(f"MP4Box output: {line}")
                all_output.append(line)

                # parse progress lines: "Import: |====| (XX/100)" or "ISO File Writing: |====| (XX/100)"
                if (
                    "Import:" in line
                    or "Importing ISO File:" in line
                    or "ISO File Writing:" in line
                ) and "(" in line:
                    try:
                        # extract progress percentage
                        progress_part = line.split("(")[-1].split("/")[0].strip()
                        current_operation_progress = int(progress_part)

                        # detect transition to next operation when progress drops from high to low
                        if (
                            current_operation_progress <= 5
                            and last_operation_progress >= 95
                        ):
                            current_operation += 1

                        last_operation_progress = current_operation_progress

                        # calculate overall progress (0-100%)
                        operation_weight = 100.0 / total_operations
                        overall_progress = (current_operation * operation_weight) + (
                            current_operation_progress * operation_weight / 100.0
                        )
                        overall_progress = min(overall_progress, 100.0)

                        # determine descriptive stage message based on current operation
                        if current_operation == 0:
                            stage = "Importing video"
                        elif current_operation <= len(job.audio_tracks):
                            track_num = current_operation
                            stage = (
                                f"Importing audio {track_num}/{len(job.audio_tracks)}"
                            )
                        elif current_operation <= len(job.audio_tracks) + len(
                            job.subtitle_tracks
                        ):
                            track_num = current_operation - len(job.audio_tracks)
                            stage = f"Importing subtitle {track_num}/{len(job.subtitle_tracks)}"
                        else:
                            stage = "Writing output file"

                        message = f"{stage} ({current_operation_progress}%) - {overall_progress:.1f}% overall"
                        LOG.debug(message)
                        self._notify_progress(overall_progress, message)
                        self.queue_manager.update_job_progress(
                            job.job_id, overall_progress, message
                        )
                    except (ValueError, IndexError):
                        pass

            return_code = process.wait()
            self.active_processes.pop(job.job_id, None)

            current_job = self.queue_manager.get_job(job.job_id)
            if current_job and current_job.status == JobStatus.CANCELLED:
                return

            if return_code == 0:
                self.queue_manager.update_job_status(job.job_id, JobStatus.COMPLETED)
                self.queue_manager.update_job_progress(job.job_id, 100.0, "Completed")
                self._notify_complete(str(job.output_file))
            else:
                # capture detailed error from all output
                error_details = "\n".join(all_output) if all_output else "Unknown error"
                error_msg = f"MP4Box exited with code {return_code}\n{error_details}"
                LOG.error(f"MP4Box failed: {error_msg}")
                self.queue_manager.update_job_status(
                    job.job_id, JobStatus.FAILED, error_msg
                )
                self._notify_error(error_msg)

        except FileNotFoundError:
            error_msg = "MP4Box not found - please install MP4Box and add to PATH"
            self.queue_manager.update_job_status(
                job.job_id, JobStatus.FAILED, error_msg
            )
            self._notify_error(error_msg)

        except Exception as e:
            error_msg = f"Muxing failed: {str(e)}"
            self.queue_manager.update_job_status(
                job.job_id, JobStatus.FAILED, error_msg
            )
            self._notify_error(error_msg)

        finally:
            if process and process.poll() is None:
                self._kill_process(process)
            self.active_processes.pop(job.job_id, None)
            # delete chapters temp file if created
            if chapters_path and chapters_path.exists():
                chapters_path.unlink()

    def _kill_process(self, process: subprocess.Popen) -> None:
        """Kill process and all children using psutil"""
        try:
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            try:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
            process.wait(timeout=2)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            try:
                process.terminate()
                process.wait(timeout=1)
            except:
                pass

    def _notify_progress(self, percent: float, message: str) -> None:
        if self.progress_callback:
            self.progress_callback.on_progress(percent, message)

    def _notify_complete(self, output: str) -> None:
        if self.progress_callback:
            self.progress_callback.on_complete(output)

    def _notify_error(self, error: str) -> None:
        if self.progress_callback:
            self.progress_callback.on_error(error)
