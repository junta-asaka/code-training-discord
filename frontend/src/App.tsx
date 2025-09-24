import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AuthGuard from "./components/AuthGuard";
import Top from "./views/Top";
import Login from "./views/Login";
import NotFound from "./views/NotFound";

const queryClient = new QueryClient();

function App() {
  return (
    // TanStack QueryのProviderでアプリ全体をラップ
    <QueryClientProvider client={queryClient}>
      {/* React RouterのBrowserRouterでアプリ全体をラップ */}
      <BrowserRouter>
        <Routes>
          {/* 認証ガードを適用 */}
          {/* トップページ */}
          <Route
            path="/"
            element={
              <AuthGuard>
                <Top />
              </AuthGuard>
            }
          />
          {/* チャンネルページ */}
          <Route
            path="/channel"
            element={
              <AuthGuard>
                <Top channel />
              </AuthGuard>
            }
          />
          {/* ログインページ */}
          <Route path="/login" element={<Login />} />
          {/* 404ページ */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
