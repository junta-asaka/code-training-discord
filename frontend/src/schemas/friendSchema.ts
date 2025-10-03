export interface Friend {
  name: string;
  username: string;
  description?: string;
  created_at: string;
  channel_id: string;
}

export type FriendsResponse = Friend[];