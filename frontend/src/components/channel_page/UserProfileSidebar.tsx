import { useFriends } from "@/hooks/useFriends";
import "@/styles/channel_page/UserProfileSidebar.scss";
import Avatar from "@mui/material/Avatar";
import { useParams } from "react-router-dom";

const UserProfileSidebar = () => {
  // useParams: URLパラメータを取得するためのフック
  const { channelId } = useParams<{ channelId: string }>();
  const { data: friends } = useFriends();

  // チャンネルIDに対応するフレンドを検索
  const currentFriend = friends?.find(
    (friend) => friend.channel_id === channelId
  );

  return (
    <aside className="userProfileSidebar">
      <Avatar className="avatar" />
      <div className="nameSection">
        <h3 className="name">{currentFriend?.name}</h3>
        <h4 className="userName">@{currentFriend?.username}</h4>
      </div>
      <div className="infoSection">
        <h5>自己紹介</h5>
        <p>{currentFriend?.description}</p>
        <h5>メンバーになった日</h5>
        <p>{currentFriend?.created_at}</p>
      </div>
    </aside>
  );
};

export default UserProfileSidebar;
