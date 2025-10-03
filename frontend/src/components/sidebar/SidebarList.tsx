import PeopleIcon from "@mui/icons-material/People";
import Channel from "./Channel";
import AddIcon from "@mui/icons-material/Add";
import StorefrontIcon from "@mui/icons-material/Storefront";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import { useFriends } from "../../hooks/useFriends";
import { useNavigate } from "react-router-dom";
import "@/styles/sidebar/SidebarList.scss";

const SidebarList = () => {
  const { data: friends, isLoading, error } = useFriends();
  const navigate = useNavigate();

  const handleFriendsClick = () => {
    navigate("/channels/@me");
  };

  return (
    <div className="sidebarList">
      <div className="searchBar">
        <p>会話に参加または作成する</p>
      </div>
      <div className="scroller">
        <ul role="list" className="content">
          <div
            className="friendsButton chanelButton"
            onClick={handleFriendsClick}
          >
            <PeopleIcon />
            <h4>フレンド</h4>
          </div>
          <div className="nitroButton chanelButton">
            <StorefrontIcon />
            <h4>Nitroに登録</h4>
          </div>
          <div className="shopButton chanelButton">
            <WhatshotIcon />
            <h4>ショップ</h4>
          </div>
          <div className="privateChannelHeader">
            <p>ダイレクトメッセージ</p>
            <AddIcon />
          </div>
          {isLoading && <p>フレンド一覧を読み込み中...</p>}
          {error && <p>フレンド一覧の取得に失敗しました</p>}
          {friends &&
            friends.map((friend, index) => (
              <Channel
                key={`${friend.username}-${index}`}
                name={friend.name}
                channelId={friend.channel_id}
              />
            ))}
        </ul>
      </div>
    </div>
  );
};

export default SidebarList;
