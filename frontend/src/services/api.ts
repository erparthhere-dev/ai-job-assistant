import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ResumeResponse {
  resume_id: string;
  raw_text: string;
  skills: string[];
  experience_years: number | null;
  education: string[];
  job_titles: string[];
  summary: string;
  chunk_count: number;
}

export interface JobPosting {
  job_id: string;
  title: string;
  company: string;
  location: string;
  description: string;
  apply_link: string | null;
  posted_at: string | null;
  employment_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  remote: boolean;
  source: string;
}

export interface JobMatch {
  job: JobPosting;
  match_score: number;
  match_reasons: string[];
  missing_skills: string[];
  cover_letter: string | null;
}

export interface JobSearchResponse {
  resume_id: string;
  total_jobs_fetched: number;
  matches: JobMatch[];
  searched_at: string;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const uploadResume = async (file: File): Promise<ResumeResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/api/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const searchJobs = async (
  resumeId: string,
  query: string,
  location: string,
  remoteOnly: boolean,
  topK: number
): Promise<JobSearchResponse> => {
  const response = await api.post('/api/jobs/search', {
    resume_id: resumeId,
    query,
    location,
    remote_only: remoteOnly,
    top_k: topK,
  });
  return response.data;
};