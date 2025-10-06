import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import ChannelPage from "@/components/channel_page/ChannelPage";
import { useFriends } from "@/hooks/useFriends";
import type { Friend } from "@/schemas/friendSchema";

// useFriendsフックとreact-router-domをモック
vi.mock("@/hooks/useFriends");
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useParams: vi.fn(),
  };
});

const mockUseFriends = vi.mocked(useFriends);
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

describe("ChannelPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("フレンドが見つかった場合", () => {
    it("given: 有効なchannelIdとフレンドデータが存在する場合, when: コンポーネントをレンダリングする, then: フレンド名とUI要素が表示される", () => {
      // Given
      const mockFriends: Friend[] = [
        {
          name: "Test Friend",
          username: "testfriend",
          created_at: "2024-01-01T00:00:00Z",
          channel_id: "channel-1",
          description: "Test description",
        },
      ];

      mockUseParams.mockReturnValue({ channelId: "channel-1" });
      mockUseFriends.mockReturnValue({
        data: mockFriends,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <ChannelPage />
        </TestWrapper>
      );

      // Then
      // CSSクラスを使ってChannelPageのヘッダー部分の名前を特定
      const channelNameElement = document.querySelector(".channelName");
      expect(channelNameElement?.textContent).toBe("Test Friend");

      // ツールバーの要素が表示されているか確認
      const searchInput = screen.getByPlaceholderText("検索");
      expect(searchInput).toBeTruthy();
    });
  });

  describe("フレンドが見つからない場合", () => {
    it("given: channelIdに対応するフレンドが存在しない場合, when: コンポーネントをレンダリングする, then: デフォルトのメッセージが表示される", () => {
      // Given
      const mockFriends: Friend[] = [
        {
          name: "Other Friend",
          username: "otherfriend",
          created_at: "2024-01-01T00:00:00Z",
          channel_id: "channel-999",
        },
      ];

      mockUseParams.mockReturnValue({ channelId: "channel-1" });
      mockUseFriends.mockReturnValue({
        data: mockFriends,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <ChannelPage />
        </TestWrapper>
      );

      // Then
      const unknownFriend = screen.getByText("不明なフレンド");
      expect(unknownFriend).toBeTruthy();
    });
  });

  describe("検索機能", () => {
    it("given: 検索バーが表示されている場合, when: 検索バーを確認する, then: プレースホルダーテキストが正しく表示される", () => {
      // Given
      mockUseParams.mockReturnValue({ channelId: "channel-1" });
      mockUseFriends.mockReturnValue({
        data: [] as Friend[],
        isLoading: false,
        error: null,
      } as unknown as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <ChannelPage />
        </TestWrapper>
      );

      // Then
      const searchInput = screen.getByPlaceholderText("検索");
      expect(searchInput).toBeTruthy();
      expect(searchInput.tagName).toBe("INPUT");
    });
  });
});
