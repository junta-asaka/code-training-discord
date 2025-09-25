import "@/styles/channel_page/ChannelPage.scss";
import ChatContent from "./ChatContent";
import UserProfileSidebar from "./UserProfileSidebar";
import PhoneIcon from "@mui/icons-material/Phone";
import VideocamIcon from "@mui/icons-material/Videocam";
import PushPinIcon from "@mui/icons-material/PushPin";
import GroupAddIcon from "@mui/icons-material/GroupAdd";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import SearchIcon from "@mui/icons-material/Search";
import Avatar from "@mui/material/Avatar";
import { useParams } from "react-router-dom";
import { useFriends } from "@/hooks/useFriends";

const ChannelPage = () => {
  // useParams: URLパラメータを取得するためのフック
  const { channelId } = useParams<{ channelId: string }>();
  const { data: friends } = useFriends();

  // チャンネルIDに対応するフレンドを検索
  const currentFriend = friends?.find(
    (friend) => friend.channel_id === channelId
  );

  const channelName = currentFriend?.name || "不明なフレンド";

  return (
    <div className="page">
      <div className="themed">
        <div className="children">
          <Avatar className="avatar" />
          <h4 className="channelName">{channelName}</h4>
        </div>
        <div className="toolbar">
          <PhoneIcon />
          <VideocamIcon />
          <PushPinIcon />
          <GroupAddIcon />
          <AccountCircleIcon />
          <div className="searchBar">
            <input type="text" placeholder="検索" />
            <SearchIcon />
          </div>
        </div>
      </div>
      <div className="tabBody">
        <ChatContent />
        <UserProfileSidebar />
      </div>
    </div>
  );
};

export default ChannelPage;
