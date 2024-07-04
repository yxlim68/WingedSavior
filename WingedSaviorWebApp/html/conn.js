export const DEBUG_VIDEO = true;
export const DEBUG_ANDROID = false;

export let BACKEND_URL;
if (DEBUG_VIDEO) {
  BACKEND_URL = "http://127.0.0.1:8766";
} else if (DEBUG_ANDROID) {
  BACKEND_URL = "http://10.0.2.2:8766";
} else {
  BACKEND_URL = "http://192.168.200.65:8766";
}

export function api(path) {
  return BACKEND_URL + path;
}

export async function checkProjectExist(projectId) {
  try {
    // server should respond 200 if exists 404 if not found
    const r = await fetch(api(`/check_project?project=${projectId}`));
    if (r.status !== 200) return false;
    return true;
  } catch (e) {
    return false;
  }
}

export async function requiredProject(cb) {
  const params = new URLSearchParams(window.location.search);
  const projectId = params.get("project");

  // TODO: redirect user to project list page

  if (!projectId) alert("No valid project found");

  const exist = await checkProjectExist(projectId);
  if (!exist) {
    alert("Invalid project");
    return;
  }

  cb(projectId);
}
