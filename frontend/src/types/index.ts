export interface User {
  id: number;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface Agent {
  id: number;
  name: string;
  description: string;
  role: string;
  capabilities: string[];
  status: 'idle' | 'busy' | 'error' | 'offline' | 'maintenance';
  max_concurrent_tasks: number;
  current_task_id: number | null;
  completed_tasks_count: number;
  failed_tasks_count: number;
  model_provider: string | null;
  model_name: string | null;
  system_prompt: string | null;
  temperature: number;
  max_tokens: number;
  created_at: string;
  updated_at: string | null;
}

export interface Task {
  id: number;
  name: string;
  description: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  required_capabilities: string[];
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  error_message: string | null;
  assigned_to: number | null;
  creator_id: number | null;
  created_at: string;
  assigned_at: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface TaskLog {
  id: number;
  task_id: number;
  event: string;
  message: string;
  level: string;
  created_at: string;
}

export interface Stats {
  agents: {
    total: number;
    idle: number;
    busy: number;
  };
  tasks: {
    total: number;
    pending: number;
    completed: number;
    failed: number;
  };
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export interface WebSocketMessage {
  type: 'agent_update' | 'task_update' | 'log' | 'connected';
  data: unknown;
  timestamp?: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  logo_url: string | null;
  plan: string;
  max_agents: number;
  max_members: number;
  monthly_token_limit: number;
  monthly_task_limit: number;
  settings: Record<string, unknown>;
  is_active: boolean;
  member_count: number;
  created_at: string;
  updated_at: string | null;
}

export interface OrgMember {
  user_id: number;
  username: string;
  email: string;
  role: string;
  joined_at: string;
}

export interface BillingPlan {
  id: number;
  name: string;
  display_name: string;
  price_monthly: number;
  price_yearly: number;
  token_limit: number;
  task_limit: number;
  agent_limit: number;
  member_limit: number;
  features: string[];
  is_active: boolean;
}

export interface UsageSummary {
  period_start: string;
  period_end: string;
  total_cost: number;
  total_tokens: number;
  total_tasks: number;
  by_type: Record<string, number>;
  by_model: Record<string, { total_cost: number; input_tokens: number; output_tokens: number }>;
}

export interface UsageRecord {
  id: number;
  user_id: number;
  org_id: number | null;
  usage_type: string;
  quantity: number;
  unit_cost: number;
  total_cost: number;
  resource_type: string | null;
  resource_id: number | null;
  model: string | null;
  usage_metadata: Record<string, unknown>;
  created_at: string;
}

export interface InvoiceLineItem {
  description: string;
  quantity: number;
  unit_cost: number;
  total: number;
}

export interface Invoice {
  id: number;
  user_id: number;
  org_id: number | null;
  period_start: string;
  period_end: string;
  total_cost: number;
  currency: string;
  status: string;
  line_items: InvoiceLineItem[];
  created_at: string;
  paid_at: string | null;
}

export interface AgentTemplate {
  id: number;
  slug: string;
  name: string;
  description: string;
  category: string;
  author: string;
  price_label: string;
  price_cents: number;
  rating: number;
  installs_count: number;
  icon_key: string;
  capabilities: string[];
  model_provider: string | null;
  model_name: string | null;
  is_public: boolean;
  created_at: string;
}

export interface TemplateInstallation {
  id: number;
  template_id: number;
  agent_id: number | null;
  installed_at: string;
}
