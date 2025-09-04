import React from "react";
import PeopleIcon from "@mui/icons-material/People";
import Channel from "./Channel";
import AddIcon from "@mui/icons-material/Add";
import StorefrontIcon from "@mui/icons-material/Storefront";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import "@/styles/sidebar/SidebarList.scss";

const SidebarList = () => {
    return (
        <div className="sidebarList">
            <div className="searchBar">
                <p>会話に参加または作成する</p>
            </div>
            <div className="scroller">
                <ul role="list" className="content">
                    <div className="friendsButton chanelButton">
                        <PeopleIcon />
                        <h4>フレンド</h4>
                    </div>
                    <div className="nitroButton chanelButton">
                        <StorefrontIcon />
                        <h4>Nitroに登録</h4>
                    </div>
                    <div className="shopButton chanelButton">
                        <WhatshotIcon />
                        <h4>ショップ</h4>
                    </div>
                    <div className="privateChannelHeader">
                        <p>ダイレクトメッセージ</p>
                        <AddIcon />
                    </div>
                    <Channel />
                    <Channel />
                    <Channel />
                </ul>
            </div>
        </div>
    );
};

export default SidebarList;
