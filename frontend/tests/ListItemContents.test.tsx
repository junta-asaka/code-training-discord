import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import ListItemContents from "@/components/page/ListItemContents";

describe("ListItemContents", () => {
  describe("プロパティの表示", () => {
    it("given: nameとusernameプロパティが渡された場合, when: コンポーネントをレンダリングする, then: 名前とユーザー名が正しく表示される", () => {
      // Given
      const mockProps = {
        name: "Test User",
        username: "user",
      };

      // When
      render(
        <BrowserRouter>
          <ListItemContents {...mockProps} />
        </BrowserRouter>
      );

      // Then
      const nameElement = screen.getByRole("heading", { level: 4 });
      const usernameElement = screen.getByText("user");

      expect(nameElement.textContent).toBe("Test User");
      expect(usernameElement).toBeTruthy();
    });

    it("given: 空文字のname・usernameが渡された場合, when: コンポーネントをレンダリングする, then: 空文字が表示される", () => {
      // Given
      const mockProps = {
        name: "",
        username: "",
      };

      // When
      render(
        <BrowserRouter>
          <ListItemContents {...mockProps} />
        </BrowserRouter>
      );

      // Then
      const nameElement = screen.getByRole("heading", { level: 4 });
      const usernameElement = document.querySelector(".accountName span");

      expect(nameElement.textContent).toBe("");
      expect(usernameElement?.textContent).toBe("");
    });
  });

  describe("CSSクラスの適用", () => {
    it("given: コンポーネントがレンダリングされた時, when: DOM構造を確認する, then: 適切なCSSクラスが適用されている", () => {
      // Given
      const mockProps = {
        name: "テストユーザー",
        username: "testuser",
      };

      // When
      render(
        <BrowserRouter>
          <ListItemContents {...mockProps} />
        </BrowserRouter>
      );

      // Then
      const listItemContents = document.querySelector(".listItemContents");
      const listItemAccount = document.querySelector(".listItemAccount");
      const accountName = document.querySelector(".accountName");
      const listItemMenu = document.querySelector(".listItemMenu");

      expect(listItemContents).toBeTruthy();
      expect(listItemAccount).toBeTruthy();
      expect(accountName).toBeTruthy();
      expect(listItemMenu).toBeTruthy();
    });
  });
});
