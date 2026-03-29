export interface ProjectStatus {
  id: number;
  name: string;
  is_default: boolean;
}

export interface ProjectPriority {
  id: number;
  name: string;
  order: number | null;
  color: string | null;
}

export interface Employee {
  id: number;
  full_name: string;
  role: string;
  telegram: string | null;
  email: string | null;
  is_active: boolean;
  notes: string | null;
  user_id: number | null;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  status: ProjectStatus;
  priority: ProjectPriority;
  manager: Employee | null;
  start_date: string | null;
  deadline_date: string | null;
  actual_start_date: string | null;
  actual_end_date: string | null;
  budget: number | null;
  spent_hours: number | null;
  progress: number;
  client_name: string | null;
  client_contact: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

export interface MeetingParticipant {
  id: number;
  employee: Employee;
}

export interface Meeting {
  id: number;
  title: string;
  scheduled_at: string;
  actual_at: string | null;
  status: string;
  meeting_link: string | null;
  notes: string | null;
  project_id: number;
  created_at: string;
  participants: MeetingParticipant[];
}

export interface User {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ActivityLog {
  id: number;
  user_id: number | null;
  user_email: string | null;
  action: string;
  entity_type: string;
  entity_id: number | null;
  entity_name: string | null;
  details: string | null;
  created_at: string;
}

export interface Attachment {
  id: number;
  entity_type: string;
  entity_id: number;
  filename: string;
  mime_type: string;
  size: number;
  uploaded_by_id: number | null;
  created_at: string;
}

export interface StatusStat {
  status: string;
  count: number;
}

export interface PriorityStat {
  priority: string;
  count: number;
  color: string | null;
}

export interface ProjectSearchResult {
  id: number;
  name: string;
  client_name: string | null;
  rank: number;
}

export interface EmployeeSearchResult {
  id: number;
  full_name: string;
  role: string;
  rank: number;
}

export interface SearchOut {
  projects: ProjectSearchResult[];
  employees: EmployeeSearchResult[];
}

export interface Stats {
  projects_total: number;
  projects_by_status: StatusStat[];
  projects_by_priority: PriorityStat[];
  employees_active: number;
  meetings_total: number;
  meetings_upcoming: number;
  projects_overdue: number;
}
