import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SidebarList from "@/components/sidebar/SidebarList";
import { useFriends } from "@/hooks/useFriends";
import type { Friend } from "@/schemas/friendSchema";

// useFriendsフックをモック
vi.mock("@/hooks/useFriends");

const mockUseFriends = vi.mocked(useFriends);

// テスト用のコンポーネントラッパー
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("SidebarList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("ローディング状態の場合", () => {
    it("given: フレンド一覧がローディング中の場合, when: コンポーネントをレンダリングする, then: ローディングメッセージが表示される", () => {
      // Given
      mockUseFriends.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <SidebarList />
        </TestWrapper>
      );

      // Then
      const loadingMessage = screen.getByText("フレンド一覧を読み込み中...");
      expect(loadingMessage).toBeTruthy();
    });
  });

  describe("エラー状態の場合", () => {
    it("given: フレンド一覧の取得でエラーが発生した場合, when: コンポーネントをレンダリングする, then: エラーメッセージが表示される", () => {
      // Given
      mockUseFriends.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Network error"),
      } as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <SidebarList />
        </TestWrapper>
      );

      // Then
      const errorMessage = screen.getByText("フレンド一覧の取得に失敗しました");
      expect(errorMessage).toBeTruthy();
    });
  });

  describe("フレンド一覧が正常に取得できた場合", () => {
    it("given: フレンド一覧が正常に取得できた場合, when: コンポーネントをレンダリングする, then: フレンドチャンネルが表示される", () => {
      // Given
      const mockFriends: Friend[] = [
        {
          name: "Test User",
          username: "user",
          created_at: "2024-01-01T00:00:00Z",
        },
        {
          name: "Test User2",
          username: "user2",
          created_at: "2024-01-02T00:00:00Z",
        },
      ];

      mockUseFriends.mockReturnValue({
        data: mockFriends,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <SidebarList />
        </TestWrapper>
      );

      // Then
      const friend1Name = screen.getByText("Test User");
      const friend2Name = screen.getByText("Test User2");

      expect(friend1Name).toBeTruthy();
      expect(friend2Name).toBeTruthy();
    });
  });

  describe("フレンド一覧が空の場合", () => {
    it("given: フレンド一覧が空配列の場合, when: コンポーネントをレンダリングする, then: フレンドチャンネルが表示されない", () => {
      // Given
      mockUseFriends.mockReturnValue({
        data: [] as Friend[],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <SidebarList />
        </TestWrapper>
      );

      // Then
      const channelItems = document.querySelectorAll(".channel");
      expect(channelItems.length).toBe(0);
    });
  });

  describe("CSSクラスの適用", () => {
    it("given: コンポーネントがレンダリングされた時, when: DOM構造を確認する, then: 適切なCSSクラスが適用されている", () => {
      // Given
      mockUseFriends.mockReturnValue({
        data: [] as Friend[],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <SidebarList />
        </TestWrapper>
      );

      // Then
      const sidebarList = document.querySelector(".sidebarList");
      const searchBar = document.querySelector(".searchBar");
      const scroller = document.querySelector(".scroller");
      const content = document.querySelector(".content");
      const friendsButton = document.querySelector(".friendsButton");
      const nitroButton = document.querySelector(".nitroButton");
      const shopButton = document.querySelector(".shopButton");
      const privateChannelHeader = document.querySelector(
        ".privateChannelHeader"
      );

      expect(sidebarList).toBeTruthy();
      expect(searchBar).toBeTruthy();
      expect(scroller).toBeTruthy();
      expect(content).toBeTruthy();
      expect(friendsButton).toBeTruthy();
      expect(nitroButton).toBeTruthy();
      expect(shopButton).toBeTruthy();
      expect(privateChannelHeader).toBeTruthy();
    });
  });
});
