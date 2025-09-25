import ChatMessage from "./ChatMessage";
import "@/styles/channel_page/ChatContent.scss";
import AddIcon from "@mui/icons-material/Add";
import CardGiftcardIcon from "@mui/icons-material/CardGiftcard";
import GifBoxIcon from "@mui/icons-material/GifBox";
import SentimentSatisfiedAltIcon from "@mui/icons-material/SentimentSatisfiedAlt";
import StickyNote2Icon from "@mui/icons-material/StickyNote2";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";

const ChatContent = () => {
  return (
    <main className="chatContent">
      <div className="scrollerContent">
        <ol className="scrollerInner">
          <ChatMessage />
          <ChatMessage />
          <ChatMessage />
          <ChatMessage />
          <ChatMessage />
          <ChatMessage />
          <ChatMessage />
          <ChatMessage />
          <ChatMessage />
          <ChatMessage />
        </ol>
      </div>
      {/* メッセージ作成 */}
      <form>
        <div className="uploadInput">
          <AddIcon />
        </div>
        <div className="textArea">
          <input type="text" placeholder="@usernameへメッセージを送信" />
        </div>
        <div className="buttons">
          <CardGiftcardIcon />
          <GifBoxIcon />
          <SentimentSatisfiedAltIcon />
          <StickyNote2Icon />
          <SportsEsportsIcon />
        </div>
      </form>
    </main>
  );
};

export default ChatContent;
