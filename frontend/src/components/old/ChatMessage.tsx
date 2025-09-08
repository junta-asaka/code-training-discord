import React from "react";
import "@/styles/ChatMessage.scss";
import Avatar from "@mui/material/Avatar";

const ChatMessage = () => {
    return (
        <div className="message">
            <Avatar />
            <div className="messageInfo">
                <h4>
                    junta
                    <span className="messageTimestamp">2025/09/02</span>
                </h4>

                <p>メッセージ本文</p>
            </div>
        </div>
    );
};

export default ChatMessage;
