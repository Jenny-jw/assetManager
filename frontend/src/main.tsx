import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { DeploymentProvider } from "./context/DeploymentContext";
import "./index.css";
import App from "./App.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AuthProvider>
      <DeploymentProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </DeploymentProvider>
    </AuthProvider>
  </StrictMode>,
);