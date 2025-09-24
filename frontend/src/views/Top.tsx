import Bar from "../components/Bar";
import Sidebar from "../components/sidebar/Sidebar";
import Page from "../components/page/Page";
import ChannelPage from "../components/page/ChannelPage";
import "@/App.scss";

interface TopProps {
  channel?: boolean;
}

const Top = ({ channel }: TopProps) => {
  return (
    <div className="App">
      {/* bar */}
      <Bar />
      {/* content */}
      <div className="content">
        <Sidebar />
        {channel ? <ChannelPage /> : <Page />}
      </div>
    </div>
  );
};

export default Top;
