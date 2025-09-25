import "@/styles/channel_page/ChannelPage.scss";
import ChatContent from "./ChatContent";
import UserProfileSidebar from "./UserProfileSidebar";

const ChannelPage = () => {
  return (
    <div className="page">
      <div className="themad"></div>
      <div className="tabBody">
        <ChatContent />
        <UserProfileSidebar />
      </div>
    </div>
  );
};

export default ChannelPage;
