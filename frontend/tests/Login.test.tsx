import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import Login from "@/views/Login";
import { useAuthStore } from "@/stores/authStore";
import * as authApi from "@/api/auth";
import type { LoginResponse } from "@/schemas/loginSchema";

// モック設定
vi.mock("@/api/auth");

const mockedAuthApi = vi.mocked(authApi);

// テスト用のコンポーネントラッパー
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
};

describe("Login", () => {
  beforeEach(() => {
    // ストアの状態をリセット
    useAuthStore.getState().logout();

    // モックをリセット
    vi.clearAllMocks();
  });
  describe("レンダリングテスト", () => {
    it("given: Loginコンポーネント, when: 初期レンダリング, then: 必要な要素が表示される", () => {
      // Given & When
      // render: コンポーネントを仮想DOMにレンダリングする関数
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // Then
      // screen: 仮想DOM上の要素を取得するためのオブジェクト
      expect(
        screen.getByRole("heading", { name: "ログイン" })
      ).toBeInTheDocument();
      expect(screen.getByLabelText("ユーザー名")).toBeInTheDocument();
      expect(screen.getByLabelText("パスワード")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "ログイン" })
      ).toBeInTheDocument();
      expect(
        screen.getByText("アカウントをお持ちでない方は")
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: "新規登録" })
      ).toBeInTheDocument();
      const usernameInput =
        screen.getByPlaceholderText("ユーザー名を入力してください");
      const passwordInput =
        screen.getByPlaceholderText("パスワードを入力してください");
      expect(usernameInput).toBeInTheDocument();
      expect(passwordInput).toBeInTheDocument();
    });
  });

  describe("バリデーションテスト", () => {
    it("given: 空のフォーム, when: 送信ボタンをクリック, then: バリデーションエラーが表示される", async () => {
      // Given
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // When
      const submitButton = screen.getByRole("button", { name: "ログイン" });
      // fireEvent: 仮想DOM上のイベントをシミュレートするための関数
      fireEvent.click(submitButton);

      // Then
      // waitFor: 非同期処理の完了を待つための関数
      await waitFor(() => {
        expect(
          screen.getByText("ユーザー名を入力してください")
        ).toBeInTheDocument();
        expect(
          screen.getByText("パスワードを入力してください")
        ).toBeInTheDocument();
      });
    });

    it("given: 長いユーザー名（51文字）, when: フォーム送信, then: ユーザー名長のエラーが表示される", async () => {
      // Given
      const longUsername = "a".repeat(51); // 51文字
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: longUsername },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      // Then
      await waitFor(() => {
        expect(
          screen.getByText("ユーザー名は50文字以内で入力してください")
        ).toBeInTheDocument();
      });
    });

    it("given: 短いパスワード（7文字）, when: フォーム送信, then: パスワード長のエラーが表示される", async () => {
      // Given
      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "1234567" },
      }); // 7文字
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      // Then
      await waitFor(() => {
        expect(
          screen.getByText("パスワードは8文字以上で入力してください")
        ).toBeInTheDocument();
      });
    });
  });

  describe("フォーム送信テスト", () => {
    it("given: 有効な認証情報, when: ログインフォーム送信, then: API呼び出しと画面遷移が正常に実行される", async () => {
      // Given
      const mockLoginResponse = {
        name: "テストユーザー",
        username: "testuser",
        access_token: "test-token",
        token_type: "Bearer",
      };
      mockedAuthApi.loginApi.mockResolvedValue(mockLoginResponse);

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      // Then
      await waitFor(() => {
        expect(mockedAuthApi.loginApi).toHaveBeenCalledWith({
          username: "testuser",
          password: "password123",
        });
      });

      // 認証ストアが更新されているか確認
      const authState = useAuthStore.getState();
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user).toEqual({
        name: "テストユーザー",
        username: "testuser",
      });
      expect(authState.accessToken).toBe("test-token");
    });

    it("given: 無効な認証情報, when: ログインフォーム送信, then: エラーメッセージが表示される", async () => {
      // Given
      const errorMessage = "認証に失敗しました";
      mockedAuthApi.loginApi.mockRejectedValue(new Error(errorMessage));

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "invaliduser" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "wrongpassword" },
      });
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      // Then
      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      // 認証ストアが更新されていないか確認
      const authState = useAuthStore.getState();
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.user).toBeNull();
      expect(authState.accessToken).toBeNull();
    });

    it("given: APIエラー（非Errorオブジェクト）, when: ログインフォーム送信, then: デフォルトエラーメッセージが表示される", async () => {
      // Given
      mockedAuthApi.loginApi.mockRejectedValue("Network error");

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      // Then
      await waitFor(() => {
        expect(screen.getByText("ログインに失敗しました")).toBeInTheDocument();
      });
    });
  });

  describe("状態管理テスト", () => {
    it("given: ログイン処理中, when: フォーム送信, then: ローディング状態が表示され、ボタンが無効化される", async () => {
      // Given
      let resolveLogin: (value: LoginResponse) => void;
      const loginPromise = new Promise<LoginResponse>((resolve) => {
        resolveLogin = resolve;
      });
      mockedAuthApi.loginApi.mockReturnValue(loginPromise);

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      // Then
      await waitFor(() => {
        const submitButton = screen.getByRole("button", {
          name: "ログイン中...",
        });
        expect(submitButton).toBeInTheDocument();
        expect(submitButton).toBeDisabled();
      });

      // ログイン処理を完了
      resolveLogin!({
        name: "テストユーザー",
        username: "testuser",
        access_token: "test-token",
        token_type: "Bearer",
      });

      await waitFor(() => {
        const submitButton = screen.getByRole("button", { name: "ログイン" });
        expect(submitButton).toBeInTheDocument();
        expect(submitButton).not.toBeDisabled();
      });
    });

    it("given: 複数回送信, when: ローディング中に再度送信ボタンクリック, then: 追加のAPI呼び出しが発生しない", async () => {
      // Given
      let resolveLogin: (value: LoginResponse) => void;
      const loginPromise = new Promise<LoginResponse>((resolve) => {
        resolveLogin = resolve;
      });
      mockedAuthApi.loginApi.mockReturnValue(loginPromise);

      render(
        <TestWrapper>
          <Login />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });

      // 最初の送信
      fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

      // ローディング中に再度送信ボタンクリック
      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "ログイン中..." })
        ).toBeDisabled();
      });

      const disabledButton = screen.getByRole("button", {
        name: "ログイン中...",
      });
      fireEvent.click(disabledButton);

      // Then
      expect(mockedAuthApi.loginApi).toHaveBeenCalledTimes(1);

      // ログイン処理を完了
      resolveLogin!({
        name: "テストユーザー",
        username: "testuser",
        access_token: "test-token",
        token_type: "Bearer",
      });
    });
  });
});
