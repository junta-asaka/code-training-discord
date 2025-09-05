import React from "react";
import "@/styles/sidebar/Sidebar.scss";
import Guilds from "./Guilds";
import SidebarList from "./SidebarList";
import Panels from "./Panels";

const Sidebar = () => {
    return (
        <div className="sidebar">
            <Guilds />
            <SidebarList />
            <Panels />
        </div>
    );
};

export default Sidebar;
