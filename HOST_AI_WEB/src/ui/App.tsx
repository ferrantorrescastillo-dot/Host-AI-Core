import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layout/AppLayout";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { HomePage } from "./pages/HomePage";
import { ComprasPage } from "./pages/ComprasPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";

export function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/eventos" element={<PlaceholderPage modulo="Eventos" />} />
        <Route path="/produccion" element={<PlaceholderPage modulo="Produccion" />} />
        <Route path="/compras" element={<ComprasPage />} />
        <Route path="/stock" element={<PlaceholderPage modulo="Stock" />} />
        <Route path="/configuracion" element={<PlaceholderPage modulo="Configuracion" />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppLayout>
  );
}
