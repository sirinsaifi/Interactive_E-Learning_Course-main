import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App.jsx";
import { AppProvider } from "./context/AppContext.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import { ProgressProvider } from "./context/ProgressContext.jsx";
import { ThemeProvider } from "./context/ThemeContext.jsx";
import { VideoPlayerProvider } from "./context/VideoPlayerContext.jsx";
import "./index.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <ProgressProvider>
            <AppProvider>
              <VideoPlayerProvider>
                <App />
              </VideoPlayerProvider>
            </AppProvider>
          </ProgressProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>
);
