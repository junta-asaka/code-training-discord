import Avatar from "@mui/material/Avatar";
import "@/styles/channel_page/ChatMessage.scss";

const ChatMessage = () => {
  return (
    <li className="chatMessage">
      <Avatar className="avatar" />
      <div className="contents">
        <div className="contentHeader">
          <h3>name</h3>
          <span>time</span>
        </div>
        <div className="messageContent">
          <span>message</span>
        </div>
      </div>
    </li>
  );
};

export default ChatMessage;
