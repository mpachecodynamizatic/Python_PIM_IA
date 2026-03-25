export interface Role {
  id: string;
  name: string;
  description: string | null;
  permissions: Record<string, string>;
  is_system: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface RoleCreate {
  name: string;
  description?: string;
  permissions?: Record<string, string>;
}

export interface RoleUpdate {
  name?: string;
  description?: string;
  permissions?: Record<string, string>;
  is_active?: boolean;
}
