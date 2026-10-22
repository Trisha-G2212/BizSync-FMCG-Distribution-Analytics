import React from "react";
import { BrowserRouter, Routes, Route, Link, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleGate from "./components/RoleGate";
import LoginPage from "./pages/LoginPage";
import ProductsPage from "./pages/ProductsPage";
import RetailersPage from "./pages/RetailersPage";
import DistributorsPage from "./pages/DistributorsPage";
import InventoryPage from "./pages/InventoryPage";
import OrdersPage from "./pages/OrdersPage";
import ExcelImportPage from "./pages/ExcelImportPage";
import DashboardPage from "./pages/DashboardPage";
import TroubleshootingPage from "./pages/TroubleshootingPage";
import "./App.css";

function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className="sidebar">
      <h1>BizSync</h1>
      <nav>
        <Link to="/">Dashboard</Link>
        <Link to="/products">Products</Link>
        <Link to="/retailers">Retailers</Link>
        <Link to="/distributors">Distributors</Link>
        <Link to="/orders">Orders</Link>
        <Link to="/inventory">Inventory</Link>
        <RoleGate allow={["ADMIN", "SALES_MANAGER"]}>
          <Link to="/excel-import">Excel Import</Link>
        </RoleGate>
        {/* Only ADMIN and ANALYST see Troubleshooting — everyone else's
            role has no reason to touch operational issue tracking. This
            is presentational only; the real enforcement will be on the
            backend router once that feature is built in Phase 11. */}
        <RoleGate allow={["ADMIN", "ANALYST"]}>
          <Link to="/troubleshooting">Troubleshooting</Link>
        </RoleGate>
      </nav>
      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-user-name">{user?.name}</div>
          <div className="sidebar-user-role">{user?.role}</div>
        </div>
        <button className="logout-button" onClick={handleLogout}>
          Log out
        </button>
      </div>
    </aside>
  );
}

function AppLayout({ children }) {
  return (
    <div className="layout">
      <Sidebar />
      <main className="content">{children}</main>
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/products" element={<ProductsPage />} />
                <Route path="/retailers" element={<RetailersPage />} />
                <Route path="/distributors" element={<DistributorsPage />} />
                <Route path="/orders" element={<OrdersPage />} />
                <Route path="/inventory" element={<InventoryPage />} />
                <Route path="/excel-import" element={<ExcelImportPage />} />
                <Route path="/troubleshooting" element={<TroubleshootingPage />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
