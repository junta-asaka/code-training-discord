import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import Page from "@/components/page/Page";
import { useCreateFriend } from "@/hooks/useFriends";

// モック設定
vi.mock("@/hooks/useFriends");
vi.mock("@/components/page/PeopleColumn", () => ({
  default: ({
    onSearchValueChange,
  }: {
    onSearchValueChange: (value: string) => void;
  }) => (
    <div data-testid="people-column">
      <input
        data-testid="search-input"
        onChange={(e) => onSearchValueChange(e.target.value)}
        placeholder="フレンド検索"
      />
    </div>
  ),
}));
vi.mock("@/components/page/NowPlayingColumn", () => ({
  default: () => <div data-testid="now-playing-column">現在アクティブ</div>,
}));

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

const mockUseCreateFriend = vi.mocked(useCreateFriend);

describe("Page", () => {
  // モックのmutateAsync関数
  const mockMutateAsync = vi.fn();

  beforeEach(() => {
    // モックをリセット
    vi.clearAllMocks();

    // デフォルトのモック実装
    mockUseCreateFriend.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any);
  });

  describe("レンダリングテスト", () => {
    it("given: Pageコンポーネント, when: 初期レンダリング, then: 必要な要素が表示される", () => {
      // Given & When
      render(
        <TestWrapper>
          <Page />
        </TestWrapper>
      );

      // Then
      expect(screen.getByText("フレンド")).toBeInTheDocument();
      expect(screen.getByText("オンライン")).toBeInTheDocument();
      expect(screen.getByText("すべて表示")).toBeInTheDocument();
      expect(screen.getByText("フレンドに追加")).toBeInTheDocument();
      expect(screen.getByTestId("people-column")).toBeInTheDocument();
      expect(screen.getByTestId("now-playing-column")).toBeInTheDocument();
    });

    it("given: ローディング状態, when: コンポーネントレンダリング, then: ローディング中のテキストが表示される", () => {
      // Given
      mockUseCreateFriend.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any);

      // When
      render(
        <TestWrapper>
          <Page />
        </TestWrapper>
      );

      // Then
      expect(screen.getByText("フレンド追加中...")).toBeInTheDocument();
    });
  });

  describe("フレンド追加機能テスト", () => {
    it("given: 有効なユーザー名入力, when: フレンドに追加ボタンクリック, then: フレンド追加APIが呼ばれ成功メッセージが表示される", async () => {
      // Given
      const username = "testuser";
      mockMutateAsync.mockResolvedValue(undefined);

      // window.alertをモック
      const mockAlert = vi.fn();
      vi.stubGlobal("alert", mockAlert);

      render(
        <TestWrapper>
          <Page />
        </TestWrapper>
      );

      // 検索フィールドに値を入力
      const searchInput = screen.getByTestId("search-input");
      fireEvent.change(searchInput, { target: { value: username } });

      // When
      const addFriendButton = screen.getByText("フレンドに追加");
      fireEvent.click(addFriendButton);

      // Then
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(username);
        expect(mockAlert).toHaveBeenCalledWith("フレンドを追加しました");
      });

      // モックをクリア
      vi.unstubAllGlobals();
    });

    it("given: 空のユーザー名, when: フレンドに追加ボタンクリック, then: エラーメッセージが表示されAPIが呼ばれない", async () => {
      // Given
      const mockAlert = vi.fn();
      vi.stubGlobal("alert", mockAlert);

      render(
        <TestWrapper>
          <Page />
        </TestWrapper>
      );

      // When
      const addFriendButton = screen.getByText("フレンドに追加");
      fireEvent.click(addFriendButton);

      // Then
      await waitFor(() => {
        expect(mockAlert).toHaveBeenCalledWith(
          "追加するフレンドのユーザー名を入力してください"
        );
        expect(mockMutateAsync).not.toHaveBeenCalled();
      });

      // モックをクリア
      vi.unstubAllGlobals();
    });

    it("given: APIエラー, when: フレンド追加実行, then: エラーメッセージが表示される", async () => {
      // Given
      const errorMessage = "ユーザーが見つかりません";
      const username = "nonexistentuser";
      mockMutateAsync.mockRejectedValue(new Error(errorMessage));

      const mockAlert = vi.fn();
      const mockConsoleError = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});
      vi.stubGlobal("alert", mockAlert);

      render(
        <TestWrapper>
          <Page />
        </TestWrapper>
      );

      // 検索フィールドに値を入力
      const searchInput = screen.getByTestId("search-input");
      fireEvent.change(searchInput, { target: { value: username } });

      // When
      const addFriendButton = screen.getByText("フレンドに追加");
      fireEvent.click(addFriendButton);

      // Then
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(username);
        expect(mockConsoleError).toHaveBeenCalledWith(
          "フレンド追加エラー:",
          new Error(errorMessage)
        );
        expect(mockAlert).toHaveBeenCalledWith(errorMessage);
      });

      // モックをクリア
      vi.unstubAllGlobals();
      mockConsoleError.mockRestore();
    });
  });

  describe("状態管理テスト", () => {
    it("given: フレンド追加処理中, when: 再度ボタンクリック, then: 重複処理が実行されない", async () => {
      // Given
      mockUseCreateFriend.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any);

      const username = "testuser";

      render(
        <TestWrapper>
          <Page />
        </TestWrapper>
      );

      // 検索フィールドに値を入力
      const searchInput = screen.getByTestId("search-input");
      fireEvent.change(searchInput, { target: { value: username } });

      // When
      const addFriendButton = screen.getByText("フレンド追加中...");
      fireEvent.click(addFriendButton);

      // Then
      expect(mockMutateAsync).not.toHaveBeenCalled();
    });
  });
});
