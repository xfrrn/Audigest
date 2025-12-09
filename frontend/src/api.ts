import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface MediaCreateRequest {
  url: string;
}

export interface MediaResponse {
  id: number;
  original_url: string;
  title: string | null;
  author: string | null;
  platform: string;
  duration: number | null;
  status: string; // 'pending' | 'processing' | 'completed' | 'failed'
  error_msg: string | null;
  created_at: string;
}

export interface TranscriptItem {
  start_time: number;
  end_time: number;
  text: string;
  speaker_label: string;
}

export interface TranscriptResponse {
  media_id: number;
  count: number;
  segments: TranscriptItem[];
}

export interface SummaryItem {
  summary_type: string;
  content: string;
  tags: string[];
  model_used: string;
  updated_at: string;
}

export interface SummaryResponse {
  media_id: number;
  summaries: SummaryItem[];
}

export default {
  async createMediaTask(url: string): Promise<MediaResponse> {
    const response = await apiClient.post<MediaResponse>('/media/', { url });
    return response.data;
  },

  async getMediaList(skip = 0, limit = 10): Promise<MediaResponse[]> {
    const response = await apiClient.get<MediaResponse[]>('/media/', {
      params: { skip, limit },
    });
    return response.data;
  },

  async getMediaDetail(id: number): Promise<MediaResponse> {
    const response = await apiClient.get<MediaResponse>(`/media/${id}`);
    return response.data;
  },

  async getMediaTranscript(id: number): Promise<TranscriptResponse> {
    const response = await apiClient.get<TranscriptResponse>(`/media/${id}/transcript`);
    return response.data;
  },
  
  // Placeholder for summary endpoint if it exists later
  // async getMediaSummary(id: number): Promise<SummaryResponse> { ... }
};

