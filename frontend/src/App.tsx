import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AuthGuard from "./components/AuthGuard";
import Top from "./views/Top";
import Login from "./views/Login";
import Register from "./views/Register";
import NotFound from "./views/NotFound";
import { Toaster } from "react-hot-toast";

const queryClient = new QueryClient();

function App() {
  return (
    // TanStack QueryのProviderでアプリ全体をラップ
    <QueryClientProvider client={queryClient}>
      <Toaster position="bottom-center" />
      {/* React RouterのBrowserRouterでアプリ全体をラップ */}
      <BrowserRouter>
        <Routes>
          {/* ルートパスから/channels/@meにリダイレクト */}
          <Route path="/" element={<Navigate to="/channels/@me" replace />} />
          {/* 認証ガードを適用 */}
          {/* トップページ */}
          <Route
            path="/channels/@me"
            element={
              <AuthGuard>
                <Top />
              </AuthGuard>
            }
          />
          {/* チャンネルページ（チャンネルID付き） */}
          <Route
            path="/channels/@me/:channelId"
            element={
              <AuthGuard>
                <Top channel />
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
          {/* 登録ページ */}
          <Route path="/register" element={<Register />} />
          {/* 404ページ */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
