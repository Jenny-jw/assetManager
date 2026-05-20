import "./App.css";
import { Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard.tsx";
import AssetList from "./pages/AssetList.tsx";
import CreateAsset from "./pages/CreateAsset";
import EditAsset from "./pages/EditAsset.tsx";
import Login from "./pages/Login.tsx";
import SignUp from "./pages/SignUp.tsx";
import ProtectedRoute from "./routes/ProtectedRoute.tsx";

function App() {
  return (
    <main>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/assets" element={<AssetList />} />
        <Route
          path="/assets/new"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <CreateAsset />
            </ProtectedRoute>
          }
        />
        <Route
          path="/assets/:id/edit"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <EditAsset />
            </ProtectedRoute>
          }
        />
      </Routes>
    </main>
  );
}

export default App;
