import { writable } from 'svelte/store';

export interface MuxJob {
	id: string;
	status: 'pending' | 'processing' | 'completed' | 'failed';
	progress: number;
	videoFile?: string;
	audioTracks: string[];
	subtitleTracks: string[];
	chapters?: string;
	outputFile: string;
	error?: string;
}

export const jobs = writable<MuxJob[]>([]);

export function addJob(job: Omit<MuxJob, 'id' | 'status' | 'progress'>) {
	const newJob: MuxJob = {
		...job,
		id: crypto.randomUUID(),
		status: 'pending',
		progress: 0
	};
	jobs.update((j) => [...j, newJob]);
	return newJob.id;
}

export function updateJobProgress(id: string, progress: number, status?: MuxJob['status']) {
	jobs.update((j) =>
		j.map((job) => (job.id === id ? { ...job, progress, ...(status && { status }) } : job))
	);
}

export function updateJobStatus(id: string, status: MuxJob['status'], error?: string) {
	jobs.update((j) => j.map((job) => (job.id === id ? { ...job, status, error } : job)));
}

export function clearCompletedJobs() {
	jobs.update((j) => j.filter((job) => job.status !== 'completed'));
}
