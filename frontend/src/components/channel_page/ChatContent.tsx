import ChatMessage from "./ChatMessage";
import "@/styles/channel_page/ChatContent.scss";
import AddIcon from "@mui/icons-material/Add";
import CardGiftcardIcon from "@mui/icons-material/CardGiftcard";
import GifBoxIcon from "@mui/icons-material/GifBox";
import SentimentSatisfiedAltIcon from "@mui/icons-material/SentimentSatisfiedAlt";
import StickyNote2Icon from "@mui/icons-material/StickyNote2";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import { useParams } from "react-router-dom";
import { useMessages } from "@/hooks/useMessages";

const ChatContent = () => {
  const { channelId } = useParams<{ channelId: string }>();
  const { data: messages, isLoading, error } = useMessages(channelId);

  return (
    <main className="chatContent">
      <div className="scrollerContent">
        <ol className="scrollerInner">
          {isLoading && <p>メッセージ一覧を読み込み中...</p>}
          {error && <p>メッセージ一覧の取得に失敗しました</p>}
          {messages?.["messages"] &&
            messages["messages"].map((message, index) => (
              <ChatMessage
                key={`${message.id}-${index}`}
                user_id={message.user_id}
                content={message.content}
                created_at={message.created_at}
              />
            ))}
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
