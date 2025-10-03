import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import ChatMessage from "@/components/channel_page/ChatMessage";
import { useAuthStore } from "@/stores/authStore";

// useAuthStoreをモック
vi.mock("@/stores/authStore");

const mockUseAuthStore = vi.mocked(useAuthStore);

describe("ChatMessage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("ユーザー名の表示", () => {
    it("given: ログインユーザーのメッセージの場合, when: コンポーネントをレンダリングする, then: ログインユーザーの名前が表示される", () => {
      // Given
      const mockUser = { id: "user1", name: "Test User", username: "testuser" };
      mockUseAuthStore.mockReturnValue({ user: mockUser });

      const messageProps = {
        user_id: "user1",
        content: "Hello World",
        created_at: "2024-01-01T00:00:00Z",
        friendUsername: "frienduser",
      };

      // When
      render(<ChatMessage {...messageProps} />);

      // Then
      const username = screen.getByText("testuser");
      expect(username).toBeTruthy();
    });

    it("given: フレンドのメッセージでfriendUsernameが渡された場合, when: コンポーネントをレンダリングする, then: フレンドのユーザー名が表示される", () => {
      // Given
      const mockUser = { id: "user1", name: "Test User", username: "testuser" };
      mockUseAuthStore.mockReturnValue({ user: mockUser });

      const messageProps = {
        user_id: "user2", // 異なるユーザーID
        content: "Hi there!",
        created_at: "2024-01-01T01:00:00Z",
        friendUsername: "frienduser",
      };

      // When
      render(<ChatMessage {...messageProps} />);

      // Then
      const username = screen.getByText("frienduser");
      expect(username).toBeTruthy();
    });
  });

  describe("メッセージ内容の表示", () => {
    it("given: メッセージが渡された場合, when: コンポーネントをレンダリングする, then: メッセージ内容が表示される", () => {
      // Given
      const mockUser = { id: "user1", name: "Test User", username: "testuser" };
      mockUseAuthStore.mockReturnValue({ user: mockUser });

      const messageProps = {
        user_id: "user1",
        content: "This is a test message",
        created_at: "2024-01-01T00:00:00Z",
        friendUsername: "frienduser",
      };

      // When
      render(<ChatMessage {...messageProps} />);

      // Then
      const messageContent = screen.getByText("This is a test message");
      expect(messageContent).toBeTruthy();
    });

    it("given: 空のメッセージが渡された場合, when: コンポーネントをレンダリングする, then: 空文字列が表示される", () => {
      // Given
      const mockUser = { id: "user1", name: "Test User", username: "testuser" };
      mockUseAuthStore.mockReturnValue({ user: mockUser });

      const messageProps = {
        user_id: "user1",
        content: "",
        created_at: "2024-01-01T00:00:00Z",
        friendUsername: "frienduser",
      };

      // When
      render(<ChatMessage {...messageProps} />);

      // Then
      const messageContent = document.querySelector(".messageContent span");
      expect(messageContent?.textContent).toBe("");
    });

    it("given: 長いメッセージが渡された場合, when: コンポーネントをレンダリングする, then: メッセージ全体が表示される", () => {
      // Given
      const mockUser = { id: "user1", name: "Test User", username: "testuser" };
      mockUseAuthStore.mockReturnValue({ user: mockUser });

      const longMessage =
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.";
      const messageProps = {
        user_id: "user1",
        content: longMessage,
        created_at: "2024-01-01T00:00:00Z",
        friendUsername: "frienduser",
      };

      // When
      render(<ChatMessage {...messageProps} />);

      // Then
      const messageContent = screen.getByText(longMessage);
      expect(messageContent).toBeTruthy();
    });
  });

  describe("作成日時の表示", () => {
    it("given: 作成日時が渡された場合, when: コンポーネントをレンダリングする, then: 作成日時が表示される", () => {
      // Given
      const mockUser = { id: "user1", name: "Test User", username: "testuser" };
      mockUseAuthStore.mockReturnValue({ user: mockUser });

      const messageProps = {
        user_id: "user1",
        content: "Test message",
        created_at: "2024-01-01T12:30:45Z",
        friendUsername: "frienduser",
      };

      // When
      render(<ChatMessage {...messageProps} />);

      // Then
      const createdAt = screen.getByText("2024-01-01T12:30:45Z");
      expect(createdAt).toBeTruthy();
    });
  });
});
