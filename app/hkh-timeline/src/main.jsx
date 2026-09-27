import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./style.css";

// No StrictMode: the engine attaches DOM listeners and a rAF loop once on
// mount (see App.jsx); StrictMode's dev-only double-invoke would attach it
// twice. It's a single long-lived page, not a component that mounts/unmounts
// repeatedly, so this trade-off is fine.
createRoot(document.getElementById("root")).render(<App />);
