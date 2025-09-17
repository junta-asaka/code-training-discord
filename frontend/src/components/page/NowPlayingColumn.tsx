import "@/styles/page/NowPlayingColumn.scss";
import EmptyCard from "./EmptyCard";

const NowPlayingColumn = () => {
    return (
        <div className="nowPlayingColumn">
            <h3>現在アクティブ</h3>
            <EmptyCard />
        </div>
    );
};

export default NowPlayingColumn;
