import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default {
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    css: false,
  },
};
