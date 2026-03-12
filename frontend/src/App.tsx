import "./App.css";
import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard.tsx";
import AssetList from "./pages/AssetList.tsx";
import CreateAsset from "./pages/CreateAsset.tsx";
import EditAsset from "./pages/EditAsset.tsx";

function App() {
  return (
    <main>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/assets" element={<AssetList />} />
        <Route path="/assets/new" element={<CreateAsset />} />
        <Route path="/assets/:id/edit" element={<EditAsset />} />
      </Routes>
    </main>
  );
}

export default App;
