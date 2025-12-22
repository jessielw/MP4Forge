import { writable } from "svelte/store";

export interface MuxJob {
  id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  videoFile?: string;
  videoLanguage?: string;
  videoTitle?: string;
  videoDelay?: number;
  audioTracks: Array<{
    filePath: string;
    language?: string;
    title?: string;
    delay?: number;
    isDefault?: boolean;
  }>;
  subtitleTracks: Array<{
    filePath: string;
    language?: string;
    title?: string;
    isDefault?: boolean;
    isForced?: boolean;
  }>;
  chapters?: string;
  outputFile: string;
  error?: string;
  createdAt?: string;
  startedAt?: string;
  completedAt?: string;
}

export const jobs = writable<MuxJob[]>([]);
let ws: WebSocket | null = null;

// initialize WebSocket connection
export function initializeWebSocket() {
  if (ws?.readyState === WebSocket.OPEN) return;

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/jobs`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log("WebSocket connected");
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (e) {
      console.error("Failed to parse WebSocket message:", e);
    }
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };

  ws.onclose = () => {
    console.log("WebSocket disconnected");
    // reconnect after 3 seconds
    setTimeout(initializeWebSocket, 3000);
  };
}

function handleWebSocketMessage(data: any) {
  switch (data.type) {
    case "init":
      // initial job list from backend
      jobs.set(data.jobs.map(normalizeJob));
      break;

    case "job_added":
      // new job added
      jobs.update((j) => [...j, normalizeJob(data.job)]);
      break;

    case "job_status_changed":
      // job status changed
      jobs.update((j) =>
        j.map((job) => (job.id === data.job.id ? normalizeJob(data.job) : job))
      );
      break;

    case "job_progress":
      // job progress update
      jobs.update((j) =>
        j.map((job) =>
          job.id === data.job.id ? { ...job, progress: data.job.progress } : job
        )
      );
      break;
  }
}

function normalizeJob(backendJob: any): MuxJob {
  return {
    id: backendJob.id,
    status: backendJob.status as MuxJob["status"],
    progress: backendJob.progress || 0,
    videoFile: backendJob.videoFile,
    videoLanguage: backendJob.videoLanguage,
    videoTitle: backendJob.videoTitle,
    videoDelay: backendJob.videoDelay,
    audioTracks: Array.isArray(backendJob.audioTracks)
      ? backendJob.audioTracks.map((t: any) =>
          typeof t === "string" ? { filePath: t } : t
        )
      : [],
    subtitleTracks: Array.isArray(backendJob.subtitleTracks)
      ? backendJob.subtitleTracks.map((t: any) =>
          typeof t === "string" ? { filePath: t } : t
        )
      : [],
    chapters: backendJob.chapters,
    outputFile: backendJob.outputFile,
    error: backendJob.error,
    createdAt: backendJob.createdAt,
    startedAt: backendJob.startedAt,
    completedAt: backendJob.completedAt,
  };
}

// fetch initial jobs from backend
export async function loadJobs() {
  try {
    const response = await fetch("/api/queue/jobs");
    if (!response.ok) throw new Error("Failed to load jobs");
    const data = await response.json();
    jobs.set(data.jobs.map(normalizeJob));
  } catch (e) {
    console.error("Failed to load jobs:", e);
  }
}

export async function addJob(job: Omit<MuxJob, "id" | "status" | "progress">) {
  try {
    const response = await fetch("/api/queue/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_file: job.videoFile,
        video_language: job.videoLanguage || null,
        video_title: job.videoTitle || null,
        video_delay: job.videoDelay || 0,
        audio_tracks: job.audioTracks,
        subtitle_tracks: job.subtitleTracks,
        chapters: job.chapters,
        output_file: job.outputFile,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to add job");
    }

    const data = await response.json();
    return data.job_id;
  } catch (e) {
    console.error("Failed to add job:", e);
    throw e;
  }
}

export function updateJobProgress(
  id: string,
  progress: number,
  status?: MuxJob["status"]
) {
  jobs.update((j) =>
    j.map((job) =>
      job.id === id ? { ...job, progress, ...(status && { status }) } : job
    )
  );
}

export function updateJobStatus(
  id: string,
  status: MuxJob["status"],
  error?: string
) {
  jobs.update((j) =>
    j.map((job) => (job.id === id ? { ...job, status, error } : job))
  );
}

export async function clearCompletedJobs() {
  try {
    const response = await fetch("/api/queue/clear-completed", {
      method: "POST",
    });

    if (!response.ok) throw new Error("Failed to clear completed jobs");

    // remove from local state
    jobs.update((j) =>
      j.filter((job) => job.status !== "completed" && job.status !== "failed")
    );
  } catch (e) {
    console.error("Failed to clear completed jobs:", e);
  }
}

export async function cancelJob(jobId: string) {
  try {
    const response = await fetch(`/api/queue/cancel/${jobId}`, {
      method: "POST",
    });

    if (!response.ok) throw new Error("Failed to cancel job");
  } catch (e) {
    console.error("Failed to cancel job:", e);
    throw e;
  }
}

export async function removeJob(jobId: string) {
  try {
    const response = await fetch(`/api/queue/remove/${jobId}`, {
      method: "DELETE",
    });

    if (!response.ok) throw new Error("Failed to remove job");

    // remove from local state
    jobs.update((j) => j.filter((job) => job.id !== jobId));
  } catch (e) {
    console.error("Failed to remove job:", e);
    throw e;
  }
}

export async function startQueueProcessing() {
  try {
    const response = await fetch("/api/queue/start", {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to start queue processing");
    }

    return true;
  } catch (e) {
    console.error("Failed to start queue processing:", e);
    throw e;
  }
}

export async function stopQueueProcessing() {
  try {
    const response = await fetch("/api/queue/stop", {
      method: "POST",
    });

    if (!response.ok) throw new Error("Failed to stop queue processing");

    return true;
  } catch (e) {
    console.error("Failed to stop queue processing:", e);
    throw e;
  }
}

export async function getQueueStatus() {
  try {
    const response = await fetch("/api/queue/status");

    if (!response.ok) throw new Error("Failed to get queue status");

    return await response.json();
  } catch (e) {
    console.error("Failed to get queue status:", e);
    return { running: false, queued_count: 0, total_count: 0 };
  }
}
