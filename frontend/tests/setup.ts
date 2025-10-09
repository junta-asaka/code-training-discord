import { vi } from "vitest";
import "@testing-library/jest-dom";

// Zustand persistのモック
Object.defineProperty(window, "localStorage", {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  writable: true,
});

// CSS modules のモック
vi.mock("@/styles/sidebar/Panels.scss", () => ({}));
