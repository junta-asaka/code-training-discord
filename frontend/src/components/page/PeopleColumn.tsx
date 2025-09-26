import SearchIcon from "@mui/icons-material/Search";
import ListItemContents from "./ListItemContents";
import "@/styles/page/PeopleColumn.scss";
import { useFriends } from "../../hooks/useFriends";

const PeopleColumn = () => {
  const { data: friends, isLoading, error } = useFriends();

  return (
    <div className="peopleColumn">
      <div className="searchBar">
        <input type="text" placeholder="検索" />
        <SearchIcon />
      </div>

      <div className="peopleList">
        <div className="sectionTitle">
          <h4>すべてのフレンド</h4>
        </div>
        <div className="peopleListItem">
          {isLoading && <p>フレンド一覧を読み込み中...</p>}
          {error && <p>フレンド一覧の取得に失敗しました</p>}
          {friends &&
            friends.map((friend, index) => (
              <ListItemContents
                key={`${friend.username}-${index}`}
                name={friend.name}
                username={friend.username}
                channelId={friend.channel_id}
              />
            ))}
        </div>
      </div>
    </div>
  );
};

export default PeopleColumn;
