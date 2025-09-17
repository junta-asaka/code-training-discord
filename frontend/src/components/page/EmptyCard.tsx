import "@/styles/page/EmptyCard.scss";

const EmptyCard = () => {
    return (
        <div className="emptyCard">
            <h4>今はまだ静かな状態です...</h4>
            <p>
                ゲームやボイスチャットなど、フレンドがアクティビティを始めたら、ここに表示します！
            </p>
        </div>
    );
};

export default EmptyCard;
