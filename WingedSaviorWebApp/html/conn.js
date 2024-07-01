export const DEBUG_VIDEO = true;

export let BACKEND_URL;
if (DEBUG_VIDEO) {
  BACKEND_URL = "http://127.0.0.1:5000";
} else {
  BACKEND_URL = "http://127.0.0.1:8766";
}

export function api(path) {
  return BACKEND_URL + path;
}
