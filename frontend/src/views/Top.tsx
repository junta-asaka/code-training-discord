import Bar from "../components/Bar";
import Sidebar from "../components/sidebar/Sidebar";
import Page from "../components/page/Page";
import "@/App.scss";

const Top = () => {
  return (
    <div className="App">
      {/* bar */}
      <Bar />
      {/* content */}
      <div className="content">
        <Sidebar />
        <Page />
      </div>
    </div>
  );
};

export default Top;
