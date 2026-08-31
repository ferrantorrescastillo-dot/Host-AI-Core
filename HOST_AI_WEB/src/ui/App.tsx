import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layout/AppLayout";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ExecutiveDashboardPage } from "./pages/ExecutiveDashboardPage";
import { HomePage } from "./pages/HomePage";
import { EventosPage } from "./pages/EventosPage";
import { ComprasPage } from "./pages/ComprasPage";
import { ProduccionPage } from "./pages/ProduccionPage";
import { ProductionStockReviewPage } from "./pages/ProductionStockReviewPage";
import { StockPage } from "./pages/StockPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { ArticulosPage } from "./pages/ArticulosPage";
import { ArticuloDetailPage } from "./pages/ArticuloDetailPage";
import { BibliotecaPage } from "./pages/BibliotecaPage";
import { ElaboracionesPage } from "./pages/ElaboracionesPage";
import { ElaboracionDetailPage } from "./pages/ElaboracionDetailPage";
import { BibliotecaPendingPage } from "./pages/BibliotecaPendingPage";
import { BibliotecaImportPage } from "./pages/BibliotecaImportPage";
import { MenusPage } from "./pages/MenusPage";
import { BibliotecaMenusPage } from "./pages/BibliotecaMenusPage";
import { BibliotecaMenuDetailPage } from "./pages/BibliotecaMenuDetailPage";
import { ReservasPage } from "./pages/ReservasPage";
import { ReservaDetailPage } from "./pages/ReservaDetailPage";

export function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/executive" element={<ExecutiveDashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/eventos" element={<EventosPage />} />
        <Route path="/reservas" element={<ReservasPage />} />
        <Route path="/reservas/:reservaId" element={<ReservaDetailPage />} />
        <Route path="/produccion" element={<ProduccionPage />} />
        <Route path="/produccion/:planId/stock" element={<ProductionStockReviewPage />} />
        <Route path="/compras" element={<ComprasPage />} />
        <Route path="/stock" element={<StockPage />} />
        <Route path="/menus" element={<MenusPage />} />
        <Route path="/articulos" element={<ArticulosPage />} />
        <Route path="/articulos/:articuloId" element={<ArticuloDetailPage />} />
        <Route path="/biblioteca" element={<BibliotecaPage />} />
        <Route path="/biblioteca/elaboraciones" element={<ElaboracionesPage />} />
        <Route path="/biblioteca/elaboraciones/:elaboracionId" element={<ElaboracionDetailPage />} />
        <Route path="/biblioteca/recetas" element={<ElaboracionesPage preset="receta" />} />
        <Route path="/biblioteca/escandallos" element={<ElaboracionesPage preset="escandallo" />} />
        <Route path="/biblioteca/fichas-tecnicas" element={<ElaboracionesPage preset="ficha" />} />
        <Route path="/biblioteca/menus" element={<BibliotecaMenusPage />} />
        <Route path="/biblioteca/menus/:menuId" element={<BibliotecaMenuDetailPage />} />
        <Route path="/biblioteca/documentacion" element={<BibliotecaPendingPage title="Documentación" detail="No hay documentos clasificados públicamente fuera de sus elaboraciones." />} />
        <Route path="/biblioteca/importaciones" element={<BibliotecaImportPage />} />
        <Route path="/configuracion" element={<PlaceholderPage modulo="Configuracion" />} />
        <Route path="/home" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppLayout>
  );
}
