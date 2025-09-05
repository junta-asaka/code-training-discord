import Bar from "./components/Bar";
import Content from "./components/Content";
import "@/App.scss";

function App() {
    return (
        <div className="App">
            {/* bar */}
            <Bar />
            {/* content */}
            <Content />
        </div>
    );
}

export default App;
