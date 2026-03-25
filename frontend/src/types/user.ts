export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;  // Dynamic roles from database
  scopes: string[];  // Deprecated but kept for backward compatibility
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface UserCreate {
  email: string;
  password: string;
  full_name: string;
  role: string;  // Dynamic role name
  scopes?: string[];  // Deprecated
}

export interface UserUpdate {
  full_name?: string;
  role?: string;  // Dynamic role name
  scopes?: string[];  // Deprecated
  is_active?: boolean;
}

export interface PasswordChange {
  current_password?: string;
  new_password: string;
}

export interface PermissionResource {
  id: string;
  label: string;
}

export interface PermissionSystem {
  resources: PermissionResource[];
  levels: string[];
  roles: Record<string, Record<string, string>>;
}
