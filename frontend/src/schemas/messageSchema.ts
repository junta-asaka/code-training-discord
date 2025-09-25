export interface Message {
  id: string;
  guil_id: string;
  name: string;
  messages: {
    id: string;
    channel_id: string;
    user_id: string;
    type: string;
    content: string;
    reference_id?: string | null;
    created_at: string;
    updated_at: string;
  }[];
}

export interface MessageCreateRequest {
  channel_id: string;
  user_id: string;
  type: string;
  content: string;
  referenced_message_id: string | null;
}

export interface MessageCreateResponse {
  id: string;
  channel_id: string;
  user_id: string;
  type: string;
  content: string;
  reference_id?: string | null;
  created_at: string;
  updated_at: string;
}

export type MessagesResponse = Message;
