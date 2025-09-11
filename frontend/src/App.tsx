import { BrowserRouter, Routes, Route } from "react-router-dom";
import Top from "./views/Top";
import Login from "./views/Login";
import NotFound from "./views/NotFound";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Top />} />
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
