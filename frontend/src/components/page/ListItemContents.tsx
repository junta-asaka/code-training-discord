import Avatar from "@mui/material/Avatar";
import MapsUgcIcon from "@mui/icons-material/MapsUgc";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import "@/styles/page/ListItemContents.scss";

interface ListItemContentsProps {
  name: string;
  username: string;
}

const ListItemContents = ({ name, username }: ListItemContentsProps) => {
  return (
    <div className="listItemContents">
      <div className="listItemAccount">
        <Avatar />
        <div className="accountName">
          <h4>{name}</h4>
          <span>{username}</span>
        </div>
      </div>

      <div className="listItemMenu">
        <MapsUgcIcon />
        <MoreVertIcon />
      </div>
    </div>
  );
};

export default ListItemContents;
