import Avatar from "@mui/material/Avatar";
import MapsUgcIcon from "@mui/icons-material/MapsUgc";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { useNavigate } from "react-router-dom";
import "@/styles/page/ListItemContents.scss";

interface ListItemContentsProps {
  name: string;
  username: string;
  channelId?: string;
}

const ListItemContents = ({
  name,
  username,
  channelId,
}: ListItemContentsProps) => {
  const navigate = useNavigate();

  const handleItemClick = () => {
    navigate(`/channels/@me/${channelId}`);
  };

  return (
    <div className="listItemContents" onClick={handleItemClick}>
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
