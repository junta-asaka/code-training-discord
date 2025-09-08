import React from "react";
import EmojiPeopleIcon from "@mui/icons-material/EmojiPeople";
import "@/styles/Title.scss";

const Title = () => {
    return (
        <div className="title">
            <div>
                <EmojiPeopleIcon />
                <p>フレンド</p>
            </div>
        </div>
    );
};

export default Title;
