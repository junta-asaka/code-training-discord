import "@/styles/channel_page/UserProfileSidebar.scss";
import Avatar from "@mui/material/Avatar";

const UserProfileSidebar = () => {
  return (
    <aside className="userProfileSidebar">
      <Avatar className="avatar" />
      <div className="nameSection">
        <h3 className="name">User Name</h3>
        <h4 className="userName">@username</h4>
      </div>
      <div className="infoSection">
        <h5>自己紹介</h5>
        <p>description</p>
        <h5>メンバーになった日</h5>
        <p>created at</p>
      </div>
    </aside>
  );
};

export default UserProfileSidebar;
