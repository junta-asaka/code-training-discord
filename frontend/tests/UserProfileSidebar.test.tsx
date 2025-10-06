import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import UserProfileSidebar from "@/components/channel_page/UserProfileSidebar";
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

describe("UserProfileSidebar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("フレンドが見つかった場合", () => {
    it("given: 有効なchannelIdとフレンドデータが存在する場合, when: コンポーネントをレンダリングする, then: フレンドの基本情報が表示される", () => {
      // Given
      const mockFriends: Friend[] = [
        {
          name: "Alice Johnson",
          username: "alicejohnson",
          description: "Web Developer passionate about React and TypeScript",
          created_at: "2024-01-15T08:30:00Z",
          channel_id: "channel-1",
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
          <UserProfileSidebar />
        </TestWrapper>
      );

      // Then
      const friendName = screen.getByText("Alice Johnson");
      const username = screen.getByText("@alicejohnson");
      const description = screen.getByText(
        "Web Developer passionate about React and TypeScript"
      );
      const createdAt = screen.getByText("2024-01-15T08:30:00Z");

      expect(friendName).toBeTruthy();
      expect(username).toBeTruthy();
      expect(description).toBeTruthy();
      expect(createdAt).toBeTruthy();
    });

    it("given: フレンドにdescriptionがない場合, when: コンポーネントをレンダリングする, then: 自己紹介セクションに空の内容が表示される", () => {
      // Given
      const mockFriends: Friend[] = [
        {
          name: "Bob Smith",
          username: "bobsmith",
          created_at: "2024-02-01T10:00:00Z",
          channel_id: "channel-2",
          // descriptionなし
        },
      ];

      mockUseParams.mockReturnValue({ channelId: "channel-2" });
      mockUseFriends.mockReturnValue({
        data: mockFriends,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <UserProfileSidebar />
        </TestWrapper>
      );

      // Then
      const friendName = screen.getByText("Bob Smith");
      const username = screen.getByText("@bobsmith");
      const descriptionText = document.querySelector(".infoSection p");

      expect(friendName).toBeTruthy();
      expect(username).toBeTruthy();
      expect(descriptionText?.textContent).toBe(""); // 空文字
    });
  });

  describe("フレンドが見つからない場合", () => {
    it("given: channelIdに対応するフレンドが存在しない場合, when: コンポーネントをレンダリングする, then: 空の内容が表示される", () => {
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
          <UserProfileSidebar />
        </TestWrapper>
      );

      // Then
      const nameElement = document.querySelector(".name");
      const usernameElement = document.querySelector(".userName");

      expect(nameElement?.textContent).toBe("");
      expect(usernameElement?.textContent).toBe("@");
    });
  });

  describe("情報セクション", () => {
    it("given: 複数のフレンドが存在する場合, when: 特定のchannelIdでレンダリングする, then: 正しいフレンドの情報のみ表示される", () => {
      // Given
      const mockFriends: Friend[] = [
        {
          name: "First Friend",
          username: "firstuser",
          description: "First description",
          created_at: "2024-01-01T00:00:00Z",
          channel_id: "channel-1",
        },
        {
          name: "Second Friend",
          username: "seconduser",
          description: "Second description",
          created_at: "2024-02-01T00:00:00Z",
          channel_id: "channel-2",
        },
      ];

      mockUseParams.mockReturnValue({ channelId: "channel-2" });
      mockUseFriends.mockReturnValue({
        data: mockFriends,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useFriends>);

      // When
      render(
        <TestWrapper>
          <UserProfileSidebar />
        </TestWrapper>
      );

      // Then
      const selectedFriendName = screen.getByText("Second Friend");
      const selectedUsername = screen.getByText("@seconduser");
      const selectedDescription = screen.getByText("Second description");

      expect(selectedFriendName).toBeTruthy();
      expect(selectedUsername).toBeTruthy();
      expect(selectedDescription).toBeTruthy();

      // 他のフレンドの情報は表示されない
      const firstFriendName = screen.queryByText("First Friend");
      expect(firstFriendName).toBeNull();
    });
  });

  describe("データの動的更新", () => {
    it("given: フレンドデータが更新された場合, when: 再レンダリングする, then: 新しいデータが表示される", () => {
      // Given
      const initialFriends: Friend[] = [
        {
          name: "Initial Friend",
          username: "initialuser",
          description: "Initial description",
          created_at: "2024-01-01T00:00:00Z",
          channel_id: "channel-1",
        },
      ];

      const updatedFriends: Friend[] = [
        {
          name: "Updated Friend",
          username: "updateduser",
          description: "Updated description",
          created_at: "2024-01-01T00:00:00Z",
          channel_id: "channel-1",
        },
      ];

      mockUseParams.mockReturnValue({ channelId: "channel-1" });
      mockUseFriends.mockReturnValue({
        data: initialFriends,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useFriends>);

      // When
      const { rerender } = render(
        <TestWrapper>
          <UserProfileSidebar />
        </TestWrapper>
      );

      // 初期状態の確認
      const initialName = screen.getByText("Initial Friend");
      expect(initialName).toBeTruthy();

      // データを更新して再レンダリング
      mockUseFriends.mockReturnValue({
        data: updatedFriends,
        isLoading: false,
        error: null,
      } as ReturnType<typeof useFriends>);

      rerender(
        <TestWrapper>
          <UserProfileSidebar />
        </TestWrapper>
      );

      // Then
      const updatedName = screen.getByText("Updated Friend");
      const updatedUsername = screen.getByText("@updateduser");
      const updatedDescription = screen.getByText("Updated description");

      expect(updatedName).toBeTruthy();
      expect(updatedUsername).toBeTruthy();
      expect(updatedDescription).toBeTruthy();
    });
  });
});
