import PeopleIcon from "@mui/icons-material/People";
import MapsUgcIcon from "@mui/icons-material/MapsUgc";
import PeopleColumn from "./PeopleColumn";
import NowPlayingColumn from "./NowPlayingColumn";
import "@/styles/page/Page.scss";
import { useState } from "react";
import { useCreateFriend } from "../../hooks/useFriends";

const Page = () => {
  const [searchUsername, setSearchUsername] = useState("");
  const createFriendMutation = useCreateFriend();

  const handleAddFriend = async () => {
    if (!searchUsername.trim()) {
      alert("追加するフレンドのユーザー名を入力してください");
      return;
    }

    if (createFriendMutation.isPending) {
      return; // 既にリクエスト中の場合は何もしない
    }

    try {
      await createFriendMutation.mutateAsync(searchUsername.trim());
      alert("フレンドを追加しました");
      setSearchUsername(""); // 成功時に検索値をクリア
    } catch (error) {
      console.error("フレンド追加エラー:", error);
      const errorMessage =
        error instanceof Error ? error.message : "フレンドの追加に失敗しました";
      alert(errorMessage);
    }
  };
  return (
    <div className="page">
      <div className="themed">
        <div className="children">
          <div className="friendIcon">
            <PeopleIcon />
            <h4>フレンド</h4>
          </div>
          <div className="onlineButton button">
            <h4>オンライン</h4>
          </div>
          <div className="allDispButton button">
            <h4>すべて表示</h4>
          </div>
          <div className="addFriend button" onClick={handleAddFriend}>
            <h4>
              {createFriendMutation.isPending
                ? "フレンド追加中..."
                : "フレンドに追加"}
            </h4>
          </div>
        </div>
        <div className="toolbar">
          <MapsUgcIcon />
        </div>
      </div>
      <div className="tabBody">
        <PeopleColumn onSearchValueChange={setSearchUsername} />
        <NowPlayingColumn />
      </div>
    </div>
  );
};

export default Page;
