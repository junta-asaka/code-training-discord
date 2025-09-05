import Bar from "./components/Bar";
import "@/App.scss";
import Sidebar from "./components/sidebar/Sidebar";
import Page from "./components/page/Page";

function App() {
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
}

export default App;
