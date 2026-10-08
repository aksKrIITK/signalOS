export interface User {
  id: string;
  organization_id: string;
  email: string;
  full_name?: string;
  role: 'OWNER' | 'ADMIN' | 'MEMBER' | 'VIEWER';
  is_active: boolean;
}

export interface ICPDefinition {
  industry?: string;
  location?: string;
  min_employees?: number;
  max_employees?: number;
  target_personas: string[];
  tech_stack_keywords?: string[];
}

export interface SignalDefinition {
  required_signals: string[];
  signal_weights?: Record<string, number>;
}

export interface CampaignProgress {
  total: number;
  processed: number;
  failed: number;
  remaining: number;
  status_breakdown: Record<string, number>;
}

export interface Campaign {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  status: 'DRAFT' | 'QUEUED' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED';
  icp_definition: ICPDefinition;
  signal_definition: SignalDefinition;
  progress?: CampaignProgress;
}

export interface Company {
  id: string;
  organization_id: string;
  name: string;
  domain: string;
  industry?: string;
  employee_count?: number;
  country?: string;
  description?: string;
  metadata?: Record<string, any>;
}

export interface Contact {
  id: string;
  organization_id: string;
  company_id: string;
  first_name: string;
  last_name?: string;
  email?: string;
  job_title?: string;
  linkedin_url?: string;
}

export interface Lead {
  id: string;
  organization_id: string;
  company_id: string;
  contact_id?: string;
  status: 'NEW' | 'RESEARCHING' | 'QUALIFIED' | 'DISQUALIFIED' | 'CONTACTED' | 'REPLIED' | 'CONVERTED';
  score?: number;
  score_reason: {
    reasons?: string[];
    signals?: string[];
    confidence?: number;
    deterministic_components?: Record<string, number>;
    qualitative_components?: Record<string, number>;
  };
  source?: string;
  company?: Company;
  contact?: Contact;
}

export interface ToolCall {
  id: string;
  agent_run_id: string;
  tool_name: string;
  arguments: Record<string, any>;
  result: Record<string, any>;
  status: string;
  latency_ms: number;
  error?: string;
  created_at: string;
}

export interface AgentRun {
  id: string;
  organization_id: string;
  campaign_id?: string;
  lead_id?: string;
  agent_type: string;
  status: 'QUEUED' | 'RUNNING' | 'WAITING_APPROVAL' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  input_json: Record<string, any>;
  output_json: {
    score?: number;
    score_reasons?: string[];
    signals?: Array<{ name: string; evidence: string; source_url?: string; confidence?: number }>;
    email_subject?: string;
    email_body?: string;
    evidence_claims?: Array<{ claim: string; source: string; confidence: number }>;
    critic_passed?: boolean;
    requires_approval?: boolean;
    action_executed?: boolean;
    action_result?: Record<string, any>;
    rejection_feedback?: string;
  };
  model?: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  started_at?: string;
  completed_at?: string;
  error?: string;
  tool_calls?: ToolCall[];
}

export interface DashboardMetrics {
  total_campaigns: number;
  total_leads: number;
  qualified_leads: number;
  total_agent_runs: number;
  success_rate_percent: number;
  total_cost_usd: number;
  total_tokens: number;
  avg_cost_per_lead_usd: number;
  avg_run_latency_seconds: number;
}
