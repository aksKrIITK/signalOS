import {
  AgentRun,
  Campaign,
  DashboardMetrics,
  Lead,
  User,
} from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('signalos_token');
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('signalos_token', token);
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP error ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.error && errorData.error.message) {
          errorMessage = errorData.error.message;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (e) {
        // use default message
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  // Dashboard Metrics
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return this.request<DashboardMetrics>('/metrics/dashboard');
  }

  // Campaigns
  async getCampaigns(): Promise<Campaign[]> {
    return this.request<Campaign[]>('/campaigns');
  }

  async getCampaign(id: string): Promise<Campaign> {
    return this.request<Campaign>(`/campaigns/${id}`);
  }

  async createCampaign(data: Partial<Campaign>): Promise<Campaign> {
    return this.request<Campaign>('/campaigns', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async runCampaign(id: string): Promise<{ job_id: string; status: string; message: string }> {
    return this.request(`/campaigns/${id}/run`, { method: 'POST' });
  }

  async pauseCampaign(id: string): Promise<Campaign> {
    return this.request(`/campaigns/${id}/pause`, { method: 'POST' });
  }

  async getCampaignProgress(id: string): Promise<any> {
    return this.request(`/campaigns/${id}/progress`);
  }

  // Leads
  async getLeads(status?: string, min_score?: number): Promise<Lead[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (min_score) params.append('min_score', min_score.toString());
    return this.request<Lead[]>(`/leads?${params.toString()}`);
  }

  async getLead(id: string): Promise<Lead> {
    return this.request<Lead>(`/leads/${id}`);
  }

  // Agent Runs & Approvals
  async getAgentRuns(status?: string): Promise<AgentRun[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    return this.request<AgentRun[]>(`/agent-runs?${params.toString()}`);
  }

  async getAgentRun(id: string): Promise<AgentRun> {
    return this.request<AgentRun>(`/agent-runs/${id}`);
  }

  async getPendingApprovals(): Promise<AgentRun[]> {
    return this.request<AgentRun[]>('/approvals');
  }

  async approveAction(id: string, editedSubject?: string, editedBody?: string): Promise<any> {
    return this.request(`/approvals/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({
        action: 'APPROVE',
        edited_subject: editedSubject,
        edited_body: editedBody,
      }),
    });
  }

  async rejectAction(id: string, feedback?: string): Promise<any> {
    return this.request(`/approvals/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({
        action: 'REJECT',
        feedback,
      }),
    });
  }

  // Knowledge & RAG
  async uploadDocument(title: string, content: string, source_url?: string): Promise<any> {
    return this.request('/knowledge/documents', {
      method: 'POST',
      body: JSON.stringify({
        title,
        content,
        source_url,
      }),
    });
  }

  async searchKnowledge(query: string, top_k: number = 5): Promise<any> {
    return this.request('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k }),
    });
  }
}

export const api = new ApiClient();
