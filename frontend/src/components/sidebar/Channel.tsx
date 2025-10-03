import "@/styles/sidebar/Channel.scss";
import Avatar from "@mui/material/Avatar";
import { useNavigate } from "react-router-dom";

interface ChannelProps {
  name: string;
  channelId?: string;
}

const Channel = ({ name, channelId }: ChannelProps) => {
  const navigate = useNavigate();

  const handleChannelClick = () => {
    navigate(`/channels/@me/${channelId}`);
  };

  return (
    <li className="channel" onClick={handleChannelClick}>
      <div className="channelAccount">
        <Avatar />
        <div className="accountName">
          <h4>{name}</h4>
        </div>
      </div>
    </li>
  );
};

export default Channel;
