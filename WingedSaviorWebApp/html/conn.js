const BACKEND_URL = "http://127.0.0.1:5000";

function api(path) {
  return BACKEND_URL + path;
}

export default {
  BACKEND_URL,
  api,
};
