import Avatar from "@mui/material/Avatar";
import "@/styles/channel_page/ChatMessage.scss";

interface ChatMessageProps {
  user_id: string;
  content: string;
  created_at: string;
}

const ChatMessage = ({ user_id, content, created_at }: ChatMessageProps) => {
  return (
    <li className="chatMessage">
      <Avatar className="avatar" />
      <div className="contents">
        <div className="contentHeader">
          <h3>{user_id}</h3>
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
