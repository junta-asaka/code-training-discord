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

const ChannelPage = () => {
  return (
    <div className="page">
      <div className="themed">
        <div className="children">
          <Avatar className="avatar" />
          <h4 className="channelName">channel-name</h4>
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
