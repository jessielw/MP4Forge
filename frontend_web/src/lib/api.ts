import type { MuxJob } from "./stores/queue";

const API_BASE = "/api";

// loglevel
enum LogLevel {
  DEBUG = 10,
  INFO = 20,
  WARNING = 30,
  ERROR = 40,
  CRITICAL = 50,
}

class ApiClient {
  /**
   * Create a WebSocket connection for job processing
   */
  static createJobWebSocket(
    job: Partial<MuxJob>,
    onProgress: (percent: number, message: string) => void,
    onComplete: (output: string) => void,
    onError: (error: string) => void
  ): WebSocket {
    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const ws = new WebSocket(`${protocol}${window.location.host}/ws/jobs`);

    ws.onopen = () => {
      // Send job data
      ws.send(
        JSON.stringify({
          video: job.videoFile,
          audio: job.audioTracks || [],
          subtitles: job.subtitleTracks || [],
          chapters: job.chapters,
          output: job.outputFile,
        })
      );
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "progress":
          onProgress(data.percent, data.message);
          break;
        case "complete":
          onComplete(data.output);
          ws.close();
          break;
        case "error":
          onError(data.error);
          ws.close();
          break;
      }
    };

    ws.onerror = () => {
      onError("WebSocket connection failed");
    };

    return ws;
  }

  /**
   * Get MediaInfo for a file
   */
  static async getMediaInfo(filePath: string): Promise<any> {
    const response = await fetch(`${API_BASE}/mediainfo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_path: filePath }),
    });

    if (!response.ok) {
      throw new Error(`Failed to get media info: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get settings from server
   */
  static async getSettings(): Promise<any> {
    const response = await fetch(`${API_BASE}/settings`);
    if (!response.ok) {
      throw new Error(`Failed to get settings: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Save settings to server
   */
  static async saveSettings(settings: any): Promise<void> {
    const response = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });

    if (!response.ok) {
      throw new Error(`Failed to save settings: ${response.statusText}`);
    }
  }

  /**
   * Send logs to backend
   */
  static async logToBackend(message: string, level: LogLevel = LogLevel.INFO) {
    fetch(`${API_BASE}/log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        level,
        message,
        context: { message: message, level: level },
      }),
    }).catch((err) => console.error("Failed to log:", err));
  }
}

export { ApiClient, LogLevel };
