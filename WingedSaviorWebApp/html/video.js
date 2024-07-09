import { api, requiredProject } from "./conn.js";

const videoSrc = document.getElementById("video-src");
const errModal = document.getElementById("errmodal");

requiredProject(async (projectId) => {
  try {
    // check connection
    const url = api("/video_feed?project=" + projectId);
    await fetch(url);

    // if success set video src html
    videoSrc.src = url;
  } catch (e) {
    errModal.style.display = "block";
    console.error(e);
  }
});
