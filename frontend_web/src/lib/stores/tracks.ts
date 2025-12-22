import { writable } from 'svelte/store';

export interface VideoTrack {
  filePath: string;
  language: string;
  title: string;
  delay: number;
  mediaInfo?: string;
  mediaInfoData?: any;
}

export interface AudioTrack {
  id: string;
  filePath: string;
  language: string;
  title: string;
  delay: number;
  isDefault: boolean;
  trackId?: number; // For multi-track MP4 inputs
  mediaInfo?: string;
  mediaInfoData?: any;
}

export interface SubtitleTrack {
  id: string;
  filePath: string;
  language: string;
  title: string;
  isDefault: boolean;
  isForced: boolean;
  trackId?: number; // For multi-track MP4 inputs
  mediaInfo?: string;
  mediaInfoData?: any;
}

export const videoTrack = writable<VideoTrack>({
  filePath: '',
  language: '',
  title: '',
  delay: 0,
  mediaInfo: undefined,
  mediaInfoData: undefined
});

export const audioTracks = writable<AudioTrack[]>([]);
export const subtitleTracks = writable<SubtitleTrack[]>([]);
export const chaptersText = writable<string>('');

// Reset all tracks (useful for clearing state)
export function resetAllTracks() {
  videoTrack.set({
    filePath: '',
    language: '',
    title: '',
    delay: 0,
    mediaInfo: undefined,
    mediaInfoData: undefined
  });
  audioTracks.set([]);
  subtitleTracks.set([]);
  chaptersText.set('');
}

// Helper to ensure only one default track
export function setDefaultAudioTrack(trackId: string) {
  audioTracks.update(tracks => 
    tracks.map(track => ({
      ...track,
      isDefault: track.id === trackId
    }))
  );
}

export function setDefaultSubtitleTrack(trackId: string) {
  subtitleTracks.update(tracks => 
    tracks.map(track => ({
      ...track,
      isDefault: track.id === trackId
    }))
  );
}
