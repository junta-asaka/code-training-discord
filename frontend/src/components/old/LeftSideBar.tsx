import React from "react";
import "@/styles/LeftSideBar.scss";
import SidebarChannel from "./SidebarChannel";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import AddIcon from "@mui/icons-material/Add";
import MicIcon from "@mui/icons-material/Mic";
import HeadphonesIcon from "@mui/icons-material/Headphones";
import SettingsIcon from "@mui/icons-material/Settings";

const LeftSideBar = () => {
    return (
        <div className="sidebar">
            <div className="sidebar-server-list">
                <div className="server-icon">
                    <img src="./react-icon.png" alt="server icon" />
                </div>
                <div className="server-icon">
                    <img src="./react-icon.png" alt="server icon" />
                </div>
            </div>

            <div className="sidebar-dm-list">
                <div className="sidebar-top">
                    <h3>Discord</h3>
                    <ExpandMoreIcon />
                </div>

                <div className="sidebar-channels">
                    <div className="sidebar-channels-header">
                        <div className="sidebar-header">
                            <ExpandMoreIcon />
                            <h4>プログラミングチャネル</h4>
                        </div>
                        <AddIcon className="sidebar-addicon" />
                    </div>

                    <div className="sidebar-channel-list">
                        <SidebarChannel />
                        <SidebarChannel />
                    </div>
                </div>

                <div className="sidebarFooter">
                    <div className="sidebarAccount">
                        <img src="./react-icon.png" alt="" />
                        <div className="accountName">
                            <h4>junta</h4>
                            <span>#8162</span>
                        </div>
                    </div>

                    <div className="sidebarVoice">
                        <MicIcon />
                        <HeadphonesIcon />
                        <SettingsIcon />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LeftSideBar;
