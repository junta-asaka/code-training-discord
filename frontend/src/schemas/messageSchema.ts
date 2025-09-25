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

export type MessagesResponse = Message;
