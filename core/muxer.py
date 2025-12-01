import platform
import subprocess
from typing import Optional
from uuid import UUID

import psutil

from core.queue_manager import JobStatus, MuxJob, QueueManager


class ProgressCallback:
    """Override this in your UI layer"""

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
        # print(job)
        # self._mock_mux_with_ping(job)
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
        """Actual MP4Box muxing implementation"""
        process = None

        try:
            self.queue_manager.update_job_status(job.job_id, JobStatus.PROCESSING)

            # check if job was cancelled before starting
            current_job = self.queue_manager.get_job(job.job_id)
            if current_job and current_job.status == JobStatus.CANCELLED:
                return

            # build MP4Box command
            cmd = ["mp4box", "-new"]  # -new creates fresh output

            # add video track
            if job.video:
                video_opts = "#video"
                if job.video.language:
                    video_opts += f":lang={job.video.language.part3}"
                video_opts += (
                    f":name={job.video.title}" if job.video.title else ":name="
                )
                if job.video.delay_ms != 0:
                    video_opts += f":delay={job.video.delay_ms}"
                cmd.extend(["-add", f"{job.video.input_file}{video_opts}"])

            # add audio tracks
            for audio in job.audio_tracks:
                audio_opts = "#audio"
                if audio.language:
                    audio_opts += f":lang={audio.language.part3}"
                audio_opts += f":name={audio.title}" if audio.title else ":name="
                if audio.delay_ms != 0:
                    audio_opts += f":delay={audio.delay_ms}"
                # TODO: add default flag support when available
                cmd.extend(["-add", f"{audio.input_file}{audio_opts}"])

            # add subtitle tracks
            for subtitle in job.subtitle_tracks:
                subtitle_opts = ""
                if subtitle.language:
                    subtitle_opts += f":lang={subtitle.language.part3}"
                subtitle_opts += (
                    f":name={subtitle.title}" if subtitle.title else ":name="
                )
                # TODO: add forced and default flag support when available
                cmd.extend(["-add", f"{subtitle.input_file}{subtitle_opts}"])

            # add chapters if present
            if job.chapters and job.chapters.chapters:
                # TODO: MP4Box expects chapters in a file (OGM format)
                # Need to:
                # 1. Write job.chapters.chapters to temp file in OGM format
                # 2. Add -chap <temp_file> to command
                # 3. Clean up temp file after processing
                pass

            # output file
            cmd.append(str(job.output_file))

            print(cmd)

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

            # monitor MP4Box output for progress
            total_frames = None
            current_frame = 0
            all_output = []

            assert (
                process.stdout is not None
            )  # TODO: remove this, only for testing for now
            for line in process.stdout:
                # check if job was cancelled
                current_job = self.queue_manager.get_job(job.job_id)
                if current_job and current_job.status == JobStatus.CANCELLED:
                    self._kill_process(process)
                    return

                line = line.strip()
                all_output.append(line)
                # print(f"MP4Box: {line}")  # debug output

                # parse MP4Box progress output
                # TODO: Test actual MP4Box output and adjust parsing
                # MP4Box typically shows: "Importing [file]: frame X/Y" or similar
                if "frame" in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == "frame" and i + 1 < len(parts):
                            try:
                                frame_info = parts[i + 1].split("/")
                                if len(frame_info) == 2:
                                    current_frame = int(frame_info[0])
                                    total_frames = int(frame_info[1])

                                    if total_frames > 0:
                                        progress = (current_frame / total_frames) * 100
                                        message = f"Processing frame {current_frame}/{total_frames}"
                                        self._notify_progress(progress, message)
                                        self.queue_manager.update_job_progress(
                                            job.job_id, progress, message
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
                print(f"MP4Box failed: {error_msg}")  # Debug output
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
