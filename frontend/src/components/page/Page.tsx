import React from "react";
import PeopleIcon from "@mui/icons-material/People";
import MapsUgcIcon from "@mui/icons-material/MapsUgc";
import PeopleColumn from "./PeopleColumn";
import NowPlayingColumn from "./NowPlayingColumn";
import "@/styles/page/Page.scss";

const Page = () => {
    return (
        <div className="page">
            <div className="themed">
                <div className="children">
                    <div className="friendButton button">
                        <PeopleIcon />
                        <h4>フレンド</h4>
                    </div>
                    <div className="onlineButton button">
                        <h4>オンライン</h4>
                    </div>
                    <div className="allDispButton button">
                        <h4>すべて表示</h4>
                    </div>
                    <div className="addFriend button">
                        <h4>フレンドに追加</h4>
                    </div>
                </div>
                <div className="toolbar">
                    <MapsUgcIcon />
                </div>
            </div>
            <div className="tabBody">
                <PeopleColumn />
                <NowPlayingColumn />
            </div>
        </div>
    );
};

export default Page;
