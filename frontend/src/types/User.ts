export const UserRole = {
  OWNER: "owner",
  ADMIN: "admin",
  USER: "user",
  GUEST: "guest",
} as const;

export type UserRole = (typeof UserRole)[keyof typeof UserRole];

export type User = {
  id: string;
  tenant_id: string;
  username: string;
  name: string;
  email: string | null;
  role: UserRole;
  created_at: string;
  is_active: boolean;
};
