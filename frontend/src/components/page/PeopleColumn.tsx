import SearchIcon from "@mui/icons-material/Search";
import ListItemContents from "./ListItemContents";
import "@/styles/page/PeopleColumn.scss";

const PeopleColumn = () => {
    return (
        <div className="peopleColumn">
            <div className="searchBar">
                <input type="text" placeholder="検索" />
                <SearchIcon />
            </div>

            <div className="peopleList">
                <div className="sectionTitle">
                    <h4>オンライン - 1</h4>
                </div>
                <div className="peopleListItem">
                    <ListItemContents />
                    <ListItemContents />
                    <ListItemContents />
                </div>
            </div>
        </div>
    );
};

export default PeopleColumn;
