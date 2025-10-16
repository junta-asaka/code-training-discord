import PeopleIcon from "@mui/icons-material/People";
import MapsUgcIcon from "@mui/icons-material/MapsUgc";
import PeopleColumn from "./PeopleColumn";
import NowPlayingColumn from "./NowPlayingColumn";
import "@/styles/page/Page.scss";
import { useState } from "react";
import { useCreateFriend } from "../../hooks/useFriends";
import toast from "react-hot-toast";
import { z, ZodError } from "zod";

// フレンド追加用のユーザー名バリデーションスキーマ
const friendUsernameSchema = z
  .string()
  .min(1, "追加するフレンドのユーザー名を入力してください")
  .max(50, "ユーザーIDは50文字以内で入力してください")
  .regex(
    /^[a-zA-Z0-9_-]+$/,
    "ユーザーIDは英数字、アンダースコア、ハイフンのみ使用できます"
  );

const Page = () => {
  const [searchUserName, setSearchUserName] = useState("");
  const createFriendMutation = useCreateFriend();

  const handleAddFriend = async () => {
    // ユーザー名のバリデーション
    try {
      friendUsernameSchema.parse(searchUserName);
    } catch (error) {
      if (error instanceof ZodError) {
        toast.error(error.issues[0].message);
      } else {
        toast.error("ユーザー名の形式が正しくありません");
      }
      return;
    }

    if (createFriendMutation.isPending) {
      return; // 既にリクエスト中の場合は何もしない
    }

    try {
      await createFriendMutation.mutateAsync(searchUserName.trim());
      toast.success("フレンドを追加しました");
      setSearchUserName(""); // 成功時に検索値をクリア
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "フレンドの追加に失敗しました";
      toast.error(errorMessage);
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
        <PeopleColumn onSearchValueChange={setSearchUserName} />
        <NowPlayingColumn />
      </div>
    </div>
  );
};

export default Page;
