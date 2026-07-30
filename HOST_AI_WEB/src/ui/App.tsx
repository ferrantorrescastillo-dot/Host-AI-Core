import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layout/AppLayout";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ExecutiveDashboardPage } from "./pages/ExecutiveDashboardPage";
import { HomePage } from "./pages/HomePage";
import { EventosPage } from "./pages/EventosPage";
import { ComprasPage } from "./pages/ComprasPage";
import { ProduccionPage } from "./pages/ProduccionPage";
import { StockPage } from "./pages/StockPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { ArticulosPage } from "./pages/ArticulosPage";
import { ArticuloDetailPage } from "./pages/ArticuloDetailPage";

export function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/executive" element={<ExecutiveDashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/eventos" element={<EventosPage />} />
        <Route path="/produccion" element={<ProduccionPage />} />
        <Route path="/compras" element={<ComprasPage />} />
        <Route path="/stock" element={<StockPage />} />
        <Route path="/articulos" element={<ArticulosPage />} />
        <Route path="/articulos/:articuloId" element={<ArticuloDetailPage />} />
        <Route path="/configuracion" element={<PlaceholderPage modulo="Configuracion" />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppLayout>
  );
}
