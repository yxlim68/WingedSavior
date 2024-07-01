import { api } from "./conn.js";
import "./jquery.min.js";

const $videoSrc = $("#video-src");
const $err = $("#errmodal");

try {
  // check connection
  const url = api("/video_feed");
  await fetch(url);

  // if success set video src html
  $videoSrc.prop("src", url);
} catch (e) {
  $err.show();
  console.error(e);
}
