import "@/styles/sidebar/Channel.scss";
import Avatar from "@mui/material/Avatar";

const Channel = () => {
    return (
        <li className="channel">
            <div className="channelAccount">
                <Avatar />
                <div className="accountName">
                    <h4>junta</h4>
                </div>
            </div>
        </li>
    );
};

export default Channel;
