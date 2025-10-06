import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import ChatContent from "@/components/channel_page/ChatContent";
import { useMessages, useCreateMessage } from "@/hooks/useMessages";
import { useAuthStore } from "@/stores/authStore";
import type { MessagesResponse } from "@/schemas/messageSchema";

// 必要なフックとストアをモック
vi.mock("@/hooks/useMessages");
vi.mock("@/stores/authStore");
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: vi.fn(),
  };
});

const mockUseMessages = vi.mocked(useMessages);
const mockUseCreateMessage = vi.mocked(useCreateMessage);
const mockUseAuthStore = vi.mocked(useAuthStore);
const { useParams } = await import("react-router-dom");
const mockUseParams = vi.mocked(useParams);

// テスト用のコンポーネントラッパー
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </BrowserRouter>
  );
};

describe("ChatContent", () => {
  const mockMutateAsync = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // デフォルトのuseCreateMessageのモック設定
    mockUseCreateMessage.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateMessage>);

    // デフォルトのuseAuthStoreのモック設定
    mockUseAuthStore.mockReturnValue({
      user: { id: "user1", name: "Test User", username: "testuser" },
    });

    // デフォルトのuseParamsのモック設定
    mockUseParams.mockReturnValue({ channelId: "channel-1" });
  });

  describe("メッセージ一覧のローディング状態", () => {
    it("given: メッセージがローディング中の場合, when: コンポーネントをレンダリングする, then: ローディングメッセージが表示される", () => {
      // Given
      mockUseMessages.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as ReturnType<typeof useMessages>);

      // When
      render(
        <TestWrapper>
          <ChatContent />
        </TestWrapper>
      );

      // Then
      const loadingMessage = screen.getByText("メッセージ一覧を読み込み中...");
      expect(loadingMessage).toBeTruthy();
    });
  });

  describe("メッセージ一覧のエラー状態", () => {
    it("given: メッセージ取得でエラーが発生した場合, when: コンポーネントをレンダリングする, then: エラーメッセージが表示される", () => {
      // Given
      mockUseMessages.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Network error"),
      } as ReturnType<typeof useMessages>);

      // When
      render(
        <TestWrapper>
          <ChatContent />
        </TestWrapper>
      );

      // Then
      const errorMessage =
        screen.getByText("メッセージ一覧の取得に失敗しました");
      expect(errorMessage).toBeTruthy();
    });
  });

  describe("メッセージ一覧の表示", () => {
    it("given: メッセージが正常に取得できた場合, when: コンポーネントをレンダリングする, then: メッセージが表示される", () => {
      // Given
      const mockMessages: MessagesResponse = {
        id: "channel-1",
        guil_id: "guild-1",
        name: "Test Channel",
        messages: [
          {
            id: "msg1",
            channel_id: "channel-1",
            user_id: "user1",
            type: "text",
            content: "Hello World",
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-01T00:00:00Z",
          },
          {
            id: "msg2",
            channel_id: "channel-1",
            user_id: "user2",
            type: "text",
            content: "Hi there!",
            created_at: "2024-01-01T01:00:00Z",
            updated_at: "2024-01-01T01:00:00Z",
          },
        ],
      };

      mockUseMessages.mockReturnValue({
        data: mockMessages,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useMessages>);

      // When
      render(
        <TestWrapper>
          <ChatContent friendUsername="testfriend" />
        </TestWrapper>
      );

      // Then
      const message1 = screen.getByText("Hello World");
      const message2 = screen.getByText("Hi there!");

      expect(message1).toBeTruthy();
      expect(message2).toBeTruthy();
    });
  });

  describe("メッセージ送信フォーム", () => {
    it("given: フォームが表示されている場合, when: メッセージ入力欄を確認する, then: プレースホルダーが表示される", () => {
      // Given
      mockUseMessages.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useMessages>);

      // When
      render(
        <TestWrapper>
          <ChatContent />
        </TestWrapper>
      );

      // Then
      const inputField =
        screen.getByPlaceholderText("@usernameへメッセージを送信");
      expect(inputField).toBeTruthy();
    });

    it("given: 有効なメッセージが入力された場合, when: フォームを送信する, then: メッセージ作成APIが呼ばれる", async () => {
      // Given
      mockUseMessages.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useMessages>);

      const { container } = render(
        <TestWrapper>
          <ChatContent />
        </TestWrapper>
      );

      const inputField = screen.getByPlaceholderText(
        "@usernameへメッセージを送信"
      ) as HTMLInputElement;
      const form = container.querySelector("form") as HTMLFormElement;

      // When
      fireEvent.change(inputField, { target: { value: "Test message" } });
      fireEvent.submit(form);

      // Then
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          channel_id: "channel-1",
          user_id: "user1",
          type: "text",
          content: "Test message",
          referenced_message_id: null,
        });
      });
    });

    it("given: 空のメッセージが入力された場合, when: フォームを送信する, then: メッセージ作成APIは呼ばれない", async () => {
      // Given
      mockUseMessages.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useMessages>);

      const { container } = render(
        <TestWrapper>
          <ChatContent />
        </TestWrapper>
      );

      const inputField = screen.getByPlaceholderText(
        "@usernameへメッセージを送信"
      ) as HTMLInputElement;
      const form = container.querySelector("form") as HTMLFormElement;

      // When
      fireEvent.change(inputField, { target: { value: "   " } }); // 空白のみ
      fireEvent.submit(form);

      // Then
      await waitFor(() => {
        expect(mockMutateAsync).not.toHaveBeenCalled();
      });
    });

    it("given: Shift+Enterキーを押下した場合, when: Enterキーイベントを発火する, then: メッセージは送信されない", async () => {
      // Given
      mockUseMessages.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useMessages>);

      render(
        <TestWrapper>
          <ChatContent />
        </TestWrapper>
      );

      const inputField = screen.getByPlaceholderText(
        "@usernameへメッセージを送信"
      ) as HTMLInputElement;

      // When
      fireEvent.change(inputField, { target: { value: "Test message" } });
      // Shift+Enterは送信しない
      fireEvent.keyPress(inputField, {
        key: "Enter",
        code: "Enter",
        keyCode: 13,
        which: 13,
        shiftKey: true, // Shiftキーが押されている
      });

      // Then
      await waitFor(() => {
        expect(mockMutateAsync).not.toHaveBeenCalled();
      });
    });

    it("given: 送信中の場合, when: 入力フィールドを確認する, then: 入力フィールドが無効化されている", () => {
      // Given
      mockUseMessages.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useMessages>);

      mockUseCreateMessage.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true, // 送信中状態
      } as unknown as ReturnType<typeof useCreateMessage>);

      // When
      render(
        <TestWrapper>
          <ChatContent />
        </TestWrapper>
      );

      // Then
      const inputField = screen.getByPlaceholderText(
        "@usernameへメッセージを送信"
      ) as HTMLInputElement;
      expect(inputField.disabled).toBe(true);
    });
  });

  describe("認証情報が不足している場合", () => {
    it("given: ユーザー情報がない場合, when: メッセージを送信しようとする, then: メッセージは送信されない", async () => {
      // Given
      mockUseAuthStore.mockReturnValue({
        user: null, // ユーザー情報なし
      });

      mockUseMessages.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useMessages>);

      const { container } = render(
        <TestWrapper>
          <ChatContent />
        </TestWrapper>
      );

      const inputField = screen.getByPlaceholderText(
        "@usernameへメッセージを送信"
      ) as HTMLInputElement;
      const form = container.querySelector("form") as HTMLFormElement;

      // When
      fireEvent.change(inputField, { target: { value: "Test message" } });
      fireEvent.submit(form);

      // Then
      await waitFor(() => {
        expect(mockMutateAsync).not.toHaveBeenCalled();
      });
    });
  });
});
