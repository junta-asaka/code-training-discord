import MicIcon from "@mui/icons-material/Mic";
import HeadphonesIcon from "@mui/icons-material/Headphones";
import SettingsIcon from "@mui/icons-material/Settings";
import { useAuthStore } from "../../stores/authStore";
import "@/styles/sidebar/Panels.scss";

const Panels = () => {
  // useAuthStore: Zustandの認証ストアを利用するためのフック
  const { user } = useAuthStore();

  return (
    <section className="panels">
      <div className="panelAccount">
        <img src="/react-icon.png" alt="ユーザーアイコン" />
        <div className="accountName">
          <h4>{user?.name || "Unknown User"}</h4>
          <span>{user?.username ? `@${user.username}` : "#0000"}</span>
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
