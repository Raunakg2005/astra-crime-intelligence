import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { ThemeProvider } from "./theme";
import "./index.css";

// apply saved theme before first paint (avoids a flash of the wrong theme)
if (localStorage.getItem("astra-theme") === "light") document.documentElement.classList.add("light");

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>,
);
