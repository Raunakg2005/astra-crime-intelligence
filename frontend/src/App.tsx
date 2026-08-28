import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Landing from "./pages/Landing";
import Overview from "./pages/Overview";
import Geospatial from "./pages/Geospatial";
import Network from "./pages/Network";
import Predictive from "./pages/Predictive";
import NlpIntel from "./pages/NlpIntel";
import Chat from "./pages/Chat";
import Firs from "./pages/Firs";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<Layout />}>
        <Route path="/overview" element={<Overview />} />
        <Route path="/geospatial" element={<Geospatial />} />
        <Route path="/network" element={<Network />} />
        <Route path="/predictive" element={<Predictive />} />
        <Route path="/nlp" element={<NlpIntel />} />
        <Route path="/firs" element={<Firs />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

