export const DEBUG_VIDEO = false;

export let BACKEND_URL;
if (DEBUG_VIDEO) {
  BACKEND_URL = "http://127.0.0.1:5000";
} else {
  BACKEND_URL = "http://127.0.0.1:8766";
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
