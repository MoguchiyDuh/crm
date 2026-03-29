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
