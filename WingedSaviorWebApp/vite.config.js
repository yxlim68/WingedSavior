import path from "path";
import { globSync } from "glob";
import { fileURLToPath } from "url";

console.log(path.join(__dirname, "html", "jquery.min.js"));
console.log(fileURLToPath(new URL("html/jquery.min.js", import.meta.url)));
export default {
  root: path.join(__dirname, "html"),
  build: {
    minify: false,
    outDir: path.join(__dirname, "dist"),
    emptyOutDir: true,
    modulePreload: false,
    target: "esnext",
    rollupOptions: {
      input: globSync(["html/*.html", "html/*.js", "html/*.css"]),
    },
  },
};
