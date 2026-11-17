import { Route, Routes } from "react-router-dom";
import Shell from "./components/layout/Shell";
import Dashboard from "./pages/Dashboard";
import LambdaFunctions from "./pages/LambdaFunctions";
import FunctionDetails from "./pages/FunctionDetails";
import Recommendations from "./pages/Recommendations";
import CostAnalysis from "./pages/CostAnalysis";
import OptimizationCenter from "./pages/OptimizationCenter";
import OptimizationHistory from "./pages/OptimizationHistory";
import Reports from "./pages/Reports";
import SettingsPage from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Dashboard />} />
        <Route path="functions" element={<LambdaFunctions />} />
        <Route path="functions/:name" element={<FunctionDetails />} />
        <Route path="recommendations" element={<Recommendations />} />
        <Route path="cost" element={<CostAnalysis />} />
        <Route path="optimize" element={<OptimizationCenter />} />
        <Route path="history" element={<OptimizationHistory />} />
        <Route path="reports" element={<Reports />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
