import ChatMessage from "./ChatMessage";
import "@/styles/channel_page/ChatContent.scss";
import AddIcon from "@mui/icons-material/Add";
import CardGiftcardIcon from "@mui/icons-material/CardGiftcard";
import GifBoxIcon from "@mui/icons-material/GifBox";
import SentimentSatisfiedAltIcon from "@mui/icons-material/SentimentSatisfiedAlt";
import StickyNote2Icon from "@mui/icons-material/StickyNote2";
import SportsEsportsIcon from "@mui/icons-material/SportsEsports";
import { useParams } from "react-router-dom";
import { useMessages, useCreateMessage } from "@/hooks/useMessages";
import { useAuthStore } from "@/stores/authStore";
import { useState } from "react";

interface ChatContentProps {
  friendUsername?: string; // フレンドのユーザー名（オプション）
}

const ChatContent = ({ friendUsername }: ChatContentProps) => {
  const { channelId } = useParams<{ channelId: string }>();
  const { data: messages, isLoading, error } = useMessages(channelId);
  const createMessage = useCreateMessage();
  const { user } = useAuthStore();
  const [inputMessage, setInputMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 空文字の場合は送信しない
    const trimmedMessage = inputMessage.trim();
    if (!trimmedMessage || !channelId || !user?.id) {
      return;
    }

    try {
      await createMessage.mutateAsync({
        channel_id: channelId,
        user_id: user.id,
        type: "text",
        content: trimmedMessage,
        referenced_message_id: null,
      });

      // 送信後、入力フィールドをクリア
      setInputMessage("");
    } catch (error) {
      console.error("メッセージ送信に失敗しました:", error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const formEvent = new Event("submit", {
        bubbles: true,
        cancelable: true,
      });
      handleSubmit(formEvent as unknown as React.FormEvent);
    }
  };

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
                friendUsername={friendUsername}
              />
            ))}
        </ol>
      </div>
      {/* メッセージ作成 */}
      <form onSubmit={handleSubmit}>
        <div className="uploadInput">
          <AddIcon />
        </div>
        <div className="textArea">
          <input
            type="text"
            placeholder="@usernameへメッセージを送信"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={createMessage.isPending}
          />
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
