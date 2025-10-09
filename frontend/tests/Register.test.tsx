import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import Register from "@/views/Register";
import * as registerApi from "@/api/register";
import type { RegisterResponse } from "@/schemas/registerSchema";

// モック設定
vi.mock("@/api/register");

const mockedRegisterApi = vi.mocked(registerApi);

// useNavigateをモック
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

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

describe("Register", () => {
  beforeEach(() => {
    // モックをリセット
    vi.clearAllMocks();
  });

  describe("レンダリングテスト", () => {
    it("given: Registerコンポーネント, when: 初期レンダリング, then: 必要な要素が表示される", () => {
      // Given & When
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // Then
      expect(
        screen.getByRole("heading", { name: "アカウントを作成" })
      ).toBeInTheDocument();
      expect(screen.getByLabelText("ユーザー名")).toBeInTheDocument();
      expect(screen.getByLabelText("ユーザーID")).toBeInTheDocument();
      expect(screen.getByLabelText("メールアドレス")).toBeInTheDocument();
      expect(screen.getByLabelText("パスワード")).toBeInTheDocument();
      expect(screen.getByLabelText("パスワード確認")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "アカウント作成" })
      ).toBeInTheDocument();
      expect(
        screen.getByText("すでにアカウントをお持ちの方は")
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: "ログイン" })
      ).toBeInTheDocument();

      // プレースホルダーテキストの確認
      expect(
        screen.getByPlaceholderText("ユーザー名を入力してください")
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("ユーザーIDを入力してください")
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("メールアドレスを入力してください")
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("パスワードを入力してください")
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("パスワードをもう一度入力してください")
      ).toBeInTheDocument();
    });
  });

  describe("バリデーションテスト", () => {
    it("given: 空のフォーム, when: 送信ボタンをクリック, then: バリデーションエラーが表示される", async () => {
      // Given
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      const submitButton = screen.getByRole("button", {
        name: "アカウント作成",
      });
      fireEvent.click(submitButton);

      // Then
      await waitFor(() => {
        expect(
          screen.getByText("ユーザー名を入力してください")
        ).toBeInTheDocument();
        expect(
          screen.getByText("ユーザーIDを入力してください")
        ).toBeInTheDocument();
        expect(
          screen.getByText("メールアドレスを入力してください")
        ).toBeInTheDocument();
        expect(
          screen.getByText("パスワードを入力してください")
        ).toBeInTheDocument();
        expect(
          screen.getByText("パスワード確認を入力してください")
        ).toBeInTheDocument();
      });
    });

    it("given: 長いユーザー名（101文字）, when: フォーム送信, then: ユーザー名長のエラーが表示される", async () => {
      // Given
      const longName = "a".repeat(101); // 101文字
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: longName },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // Then
      await waitFor(() => {
        expect(
          screen.getByText("ユーザー名は100文字以内で入力してください")
        ).toBeInTheDocument();
      });
    });

    it("given: 長いユーザーID（51文字）, when: フォーム送信, then: ユーザーID長のエラーが表示される", async () => {
      // Given
      const longUsername = "a".repeat(51); // 51文字
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "テストユーザー" },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: longUsername },
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // Then
      await waitFor(() => {
        expect(
          screen.getByText("ユーザーIDは50文字以内で入力してください")
        ).toBeInTheDocument();
      });
    });

    it("given: 無効な文字を含むユーザーID, when: フォーム送信, then: ユーザーID形式のエラーが表示される", async () => {
      // Given
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "テストユーザー" },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: "test@user" }, // 無効文字（@）を含む
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // Then
      await waitFor(() => {
        expect(
          screen.getByText(
            "ユーザーIDは英数字、アンダースコア、ハイフンのみ使用できます"
          )
        ).toBeInTheDocument();
      });
    });

    it("given: 英字のみのパスワード, when: フォーム送信, then: パスワード形式のエラーが表示される", async () => {
      // Given
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "テストユーザー" },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password" }, // 数字なし
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password" },
      });
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // Then
      await waitFor(() => {
        expect(
          screen.getByText("パスワードは英字と数字を含む必要があります")
        ).toBeInTheDocument();
      });
    });

    it("given: 一致しないパスワード確認, when: フォーム送信, then: パスワード不一致のエラーが表示される", async () => {
      // Given
      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "テストユーザー" },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password456" }, // 異なるパスワード
      });
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // Then
      await waitFor(() => {
        expect(
          screen.getByText("パスワードが一致しません")
        ).toBeInTheDocument();
      });
    });
  });

  describe("フォーム送信テスト", () => {
    it("given: 有効な登録情報, when: 登録フォーム送信, then: API呼び出しと画面遷移が正常に実行される", async () => {
      // Given
      const mockRegisterResponse: RegisterResponse = {
        id: "user-id-123",
        name: "テストユーザー",
        username: "testuser",
        email: "test@example.com",
        message: "登録完了",
      };
      mockedRegisterApi.registerApi.mockResolvedValue(mockRegisterResponse);

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "テストユーザー" },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // Then
      await waitFor(() => {
        expect(mockedRegisterApi.registerApi).toHaveBeenCalledWith({
          name: "テストユーザー",
          username: "testuser",
          email: "test@example.com",
          password: "password123",
          confirmPassword: "password123",
        });
      });

      // 画面遷移が実行されているか確認
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith("/login", {
          replace: true,
          state: {
            message: "アカウントが作成されました。ログインしてください。",
          },
        });
      });
    });

    it("given: 無効な登録情報, when: 登録フォーム送信, then: エラーメッセージが表示される", async () => {
      // Given
      const errorMessage = "ユーザー名が既に使用されています";
      mockedRegisterApi.registerApi.mockRejectedValue(new Error(errorMessage));

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "テストユーザー" },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: "duplicateuser" },
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // Then
      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      // 画面遷移が実行されていないか確認
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it("given: APIエラー（非Errorオブジェクト）, when: 登録フォーム送信, then: デフォルトエラーメッセージが表示される", async () => {
      // Given
      mockedRegisterApi.registerApi.mockRejectedValue("Network error");

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "テストユーザー" },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // Then
      await waitFor(() => {
        expect(screen.getByText("登録に失敗しました")).toBeInTheDocument();
      });
    });
  });

  describe("状態管理テスト", () => {
    it("given: 登録処理中, when: フォーム送信, then: ローディング状態が表示され、ボタンが無効化される", async () => {
      // Given
      let resolveRegister: (value: RegisterResponse) => void;
      const registerPromise = new Promise<RegisterResponse>((resolve) => {
        resolveRegister = resolve;
      });
      mockedRegisterApi.registerApi.mockReturnValue(registerPromise);

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "テストユーザー" },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // Then
      await waitFor(() => {
        const submitButton = screen.getByRole("button", {
          name: "登録中...",
        });
        expect(submitButton).toBeInTheDocument();
        expect(submitButton).toBeDisabled();
      });

      // 登録処理を完了
      resolveRegister!({
        id: "user-id-123",
        name: "テストユーザー",
        username: "testuser",
        email: "test@example.com",
        message: "登録完了",
      });

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith("/login", {
          replace: true,
          state: {
            message: "アカウントが作成されました。ログインしてください。",
          },
        });
      });
    });

    it("given: 複数回送信, when: ローディング中に再度送信ボタンクリック, then: 追加のAPI呼び出しが発生しない", async () => {
      // Given
      let resolveRegister: (value: RegisterResponse) => void;
      const registerPromise = new Promise<RegisterResponse>((resolve) => {
        resolveRegister = resolve;
      });
      mockedRegisterApi.registerApi.mockReturnValue(registerPromise);

      render(
        <TestWrapper>
          <Register />
        </TestWrapper>
      );

      // When
      fireEvent.change(screen.getByLabelText("ユーザー名"), {
        target: { value: "テストユーザー" },
      });
      fireEvent.change(screen.getByLabelText("ユーザーID"), {
        target: { value: "testuser" },
      });
      fireEvent.change(screen.getByLabelText("メールアドレス"), {
        target: { value: "test@example.com" },
      });
      fireEvent.change(screen.getByLabelText("パスワード"), {
        target: { value: "password123" },
      });
      fireEvent.change(screen.getByLabelText("パスワード確認"), {
        target: { value: "password123" },
      });

      // 最初の送信
      fireEvent.click(screen.getByRole("button", { name: "アカウント作成" }));

      // ローディング中に再度送信ボタンクリック
      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "登録中..." })
        ).toBeDisabled();
      });

      const disabledButton = screen.getByRole("button", {
        name: "登録中...",
      });
      fireEvent.click(disabledButton);

      // Then
      expect(mockedRegisterApi.registerApi).toHaveBeenCalledTimes(1);

      // 登録処理を完了
      resolveRegister!({
        id: "user-id-123",
        name: "テストユーザー",
        username: "testuser",
        email: "test@example.com",
        message: "登録完了",
      });
    });
  });
});
