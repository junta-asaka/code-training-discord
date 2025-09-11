import Avatar from "@mui/material/Avatar";
import MapsUgcIcon from "@mui/icons-material/MapsUgc";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import "@/styles/page/ListItemContents.scss";

const ListItemContents = () => {
    return (
        <div className="listItemContents">
            <div className="listItemAccount">
                <Avatar />
                <div className="accountName">
                    <h4>junta</h4>
                    <span>#8162</span>
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
