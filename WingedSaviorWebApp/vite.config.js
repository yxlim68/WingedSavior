import path from "path";
import { glob, globSync } from "glob";

export default {
  root: path.join(__dirname, "html"),
  build: {
    outDir: path.join(__dirname, "dist"),
    target: "esnext",
    emptyOutDir: true,
    rollupOptions: {
      input: globSync("html/*.html"),
    },
  },
};
