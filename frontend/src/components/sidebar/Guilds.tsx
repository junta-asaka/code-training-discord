import "@/styles/sidebar/Guilds.scss";
import Server from "./Server";

const Guilds = () => {
  return (
    <nav className="guilds">
      <div className="dmIcon">
        <img src="/react-icon.png" alt="" />
      </div>

      <div className="serverList">
        <Server />
        <Server />
        <Server />
      </div>
    </nav>
  );
};

export default Guilds;
