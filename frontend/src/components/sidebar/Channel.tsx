import "@/styles/sidebar/Channel.scss";
import Avatar from "@mui/material/Avatar";

interface ChannelProps {
  name: string;
}

const Channel = ({ name }: ChannelProps) => {
  return (
    <li className="channel">
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
