import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

// httpOnly cookies are the only auth transport. No localStorage tokens.
const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

export default api;
