import "./App.css";
import { Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard.tsx";
import AssetList from "./pages/AssetList.tsx";
import CreateAsset from "./pages/CreateAsset";
import EditAsset from "./pages/EditAsset.tsx";
import Login from "./pages/Login.tsx";
import SignUp from "./pages/SignUp.tsx";
import ModuleRoute from "./routes/ModuleRoute.tsx";
import { UserRole } from "./types/User.ts";

const OWNER_ROLES = [UserRole.OWNER] as const;

function App() {
  return (
    <main>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route
          path="/dashboard"
          element={
            <ModuleRoute>
              <Dashboard />
            </ModuleRoute>
          }
        />
        <Route
          path="/assets"
          element={
            <ModuleRoute allowedRoles={[...OWNER_ROLES]} requireModule="inventory">
              <AssetList />
            </ModuleRoute>
          }
        />
        <Route
          path="/assets/new"
          element={
            <ModuleRoute allowedRoles={[...OWNER_ROLES]} requireModule="inventory">
              <CreateAsset />
            </ModuleRoute>
          }
        />
        <Route
          path="/assets/:id/edit"
          element={
            <ModuleRoute allowedRoles={[...OWNER_ROLES]} requireModule="inventory">
              <EditAsset />
            </ModuleRoute>
          }
        />
      </Routes>
    </main>
  );
}

export default App;
