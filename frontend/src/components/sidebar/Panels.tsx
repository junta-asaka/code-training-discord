import MicIcon from "@mui/icons-material/Mic";
import HeadphonesIcon from "@mui/icons-material/Headphones";
import SettingsIcon from "@mui/icons-material/Settings";
import "@/styles/sidebar/Panels.scss";

const Panels = () => {
    return (
        <section className="panels">
            <div className="panelAccount">
                <img src="./react-icon.png" alt="" />
                <div className="accountName">
                    <h4>junta</h4>
                    <span>#8162</span>
                </div>
            </div>

            <div className="panelVoice">
                <MicIcon />
                <HeadphonesIcon />
                <SettingsIcon />
            </div>
        </section>
    );
};

export default Panels;
