/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": "/src",
        },
    },
    server: {
        cors: {
            origin: ["http://localhost:8000", "http://localhost:5173"],
            credentials: true,
        },
    },
    test: {
        globals: true,
        environment: "jsdom",
        setupFiles: ["./tests/setup.ts"],
        include: ["./tests/*.test.tsx"],
    },
});
