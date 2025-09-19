import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Channel from "@/components/sidebar/Channel";

describe("Channel", () => {
  describe("プロパティの表示", () => {
    it("given: nameプロパティが渡された場合, when: コンポーネントをレンダリングする, then: 名前が正しく表示される", () => {
      // Given
      const mockProps = {
        name: "Test User",
      };

      // When
      render(<Channel {...mockProps} />);

      // Then
      const nameElement = screen.getByRole("heading", { level: 4 });
      expect(nameElement.textContent).toBe("Test User");
    });

    it("given: 空文字のnameが渡された場合, when: コンポーネントをレンダリングする, then: 空文字が表示される", () => {
      // Given
      const mockProps = {
        name: "",
      };

      // When
      render(<Channel {...mockProps} />);

      // Then
      const nameElement = screen.getByRole("heading", { level: 4 });
      expect(nameElement.textContent).toBe("");
    });

    it("given: 特殊文字を含む名前が渡された場合, when: コンポーネントをレンダリングする, then: 特殊文字も正しく表示される", () => {
      // Given
      const mockProps = {
        name: "Test@User#123!",
      };

      // When
      render(<Channel {...mockProps} />);

      // Then
      const nameElement = screen.getByRole("heading", { level: 4 });
      expect(nameElement.textContent).toBe("Test@User#123!");
    });
  });

  describe("CSSクラスの適用", () => {
    it("given: コンポーネントがレンダリングされた時, when: DOM構造を確認する, then: 適切なCSSクラスが適用されている", () => {
      // Given
      const mockProps = {
        name: "テストユーザー",
      };

      // When
      render(<Channel {...mockProps} />);

      // Then
      const channel = document.querySelector(".channel");
      const channelAccount = document.querySelector(".channelAccount");
      const accountName = document.querySelector(".accountName");

      expect(channel).toBeTruthy();
      expect(channelAccount).toBeTruthy();
      expect(accountName).toBeTruthy();
    });
  });

  describe("レンダリングの安定性", () => {
    it("given: 複数回レンダリングした場合, when: 同じpropsを渡す, then: 一貫した結果が得られる", () => {
      // Given
      const mockProps = {
        name: "Test User",
      };

      // When
      const { rerender } = render(<Channel {...mockProps} />);
      const firstRender = screen.getByRole("heading", { level: 4 }).textContent;

      rerender(<Channel {...mockProps} />);
      const secondRender = screen.getByRole("heading", {
        level: 4,
      }).textContent;

      // Then
      expect(firstRender).toBe(secondRender);
      expect(firstRender).toBe("Test User");
    });
  });
});
