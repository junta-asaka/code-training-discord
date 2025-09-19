import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { useAuthStore } from "@/stores/authStore";
import Panels from "@/components/sidebar/Panels";

describe("Panels", () => {
  // テストごとにストアの状態をリセット
  beforeEach(() => {
    useAuthStore.getState().logout();
  });

  describe("ユーザー情報が存在する場合", () => {
    it("given: ユーザー情報がストアに存在する, when: コンポーネントをレンダリングする, then: ユーザー名・ユーザーネーム・アカウント画像が正しく表示される", () => {
      // Given
      const mockUser = {
        id: "user-id-123",
        name: "テストユーザー",
        username: "testuser",
      };
      useAuthStore.getState().setAuth(mockUser, "test-token");

      // When
      render(<Panels />);

      // Then
      const heading = screen.getByRole("heading", { level: 4 });
      expect(heading.textContent).toBe("テストユーザー");
      const usernameElement = screen.getByText("@testuser");
      expect(usernameElement).toBeTruthy();
      const accountImage = document.querySelector("img");
      expect(accountImage).toBeTruthy();
      expect(accountImage?.getAttribute("src")).toBe("./react-icon.png");
      expect(accountImage?.getAttribute("alt")).toBe("");
    });
  });

  describe("ユーザー情報が存在しない場合", () => {
    it("given: ユーザー情報がnullの場合, when: コンポーネントをレンダリングする, then: デフォルトの値が表示される", () => {
      // Given
      useAuthStore.getState().logout();

      // When
      render(<Panels />);

      // Then
      const heading = screen.getByRole("heading", { level: 4 });
      expect(heading.textContent).toBe("Unknown User");
      const usernameElement = screen.getByText("#0000");
      expect(usernameElement).toBeTruthy();
    });

    it("given: ユーザーのname・usernameが空文字の場合, when: コンポーネントをレンダリングする, then: Unknown User・#0000が表示される", () => {
      // Given
      const mockUser = {
        id: "",
        name: "",
        username: "",
      };
      useAuthStore.getState().setAuth(mockUser, "test-token");

      // When
      render(<Panels />);

      // Then
      const heading = screen.getByRole("heading", { level: 4 });
      expect(heading.textContent).toBe("Unknown User");
      const usernameElement = screen.getByText("#0000");
      expect(usernameElement).toBeTruthy();
    });
  });

  describe("ボイスパネルの表示", () => {
    it("given: コンポーネントがレンダリングされた時, when: ボイスパネルセクションを確認する, then: 3つのアイコンが表示される", () => {
      // Given
      useAuthStore.getState().logout();

      // When
      render(<Panels />);

      // Then
      // MUIアイコンが実際にレンダリングされているかSVG要素で確認
      const svgIcons = document.querySelectorAll("svg");
      expect(svgIcons.length).toBe(3);
    });
  });

  describe("CSSクラスの適用", () => {
    it("given: コンポーネントがレンダリングされた時, when: DOM構造を確認する, then: 適切なCSSクラスが適用されている", () => {
      // Given
      useAuthStore.getState().logout();

      // When
      render(<Panels />);

      // Then
      const panelsSection = document.querySelector(".panels");
      expect(panelsSection).toBeTruthy();

      const panelAccount = document.querySelector(".panelAccount");
      expect(panelAccount).toBeTruthy();

      const accountName = document.querySelector(".accountName");
      expect(accountName).toBeTruthy();

      const panelVoice = document.querySelector(".panelVoice");
      expect(panelVoice).toBeTruthy();
    });
  });
});
