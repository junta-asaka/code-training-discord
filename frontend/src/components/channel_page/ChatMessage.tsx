import Avatar from "@mui/material/Avatar";
import "@/styles/channel_page/ChatMessage.scss";
import { useAuthStore } from "@/stores/authStore";
import { useMemo } from "react";

interface ChatMessageProps {
  user_id: string;
  content: string;
  created_at: string;
  friendUsername?: string; // フレンドのユーザー名（オプション）
}

const ChatMessage = ({
  user_id,
  content,
  created_at,
  friendUsername,
}: ChatMessageProps) => {
  const { user } = useAuthStore();

  // user_idからusernameを検索する
  // useMemo: Reactのフックで、計算コストの高い関数の結果をメモ化するために使用
  const username = useMemo(() => {
    // 現在のログインユーザーのIDと一致する場合
    if (user && user.id === user_id) {
      return user.username;
    }
    // フレンドのユーザー名が渡された場合は、それを使用
    else if (friendUsername) {
      return friendUsername;
    }

    // フォールバックとしてuser_idを表示
    return user_id;
  }, [user_id, user, friendUsername]);

  return (
    <li className="chatMessage">
      <Avatar className="avatar" />
      <div className="contents">
        <div className="contentHeader">
          <h3>{username}</h3>
          <span>{created_at}</span>
        </div>
        <div className="messageContent">
          <span>{content}</span>
        </div>
      </div>
    </li>
  );
};

export default ChatMessage;
