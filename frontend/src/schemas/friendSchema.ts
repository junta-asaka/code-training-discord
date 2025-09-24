export interface Friend {
  name: string;
  username: string;
  description?: string;
  created_at: string;
}

export type FriendsResponse = Friend[];