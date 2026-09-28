import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/stores/auth";
import { AppShell } from "@/components/AppShell";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ResearchPage } from "@/pages/ResearchPage";
import { ResearchDetailPage } from "@/pages/ResearchDetailPage";
import { ResearchProjectPage } from "@/pages/ResearchProjectPage";
import {
  SourcesPage,
  CompetitorsPage,
  TrendsPage,
  ReportsPage,
  SettingsPage,
} from "@/pages/SimplePages";
import type { ReactNode } from "react";

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/research" element={<ResearchPage />} />
        <Route path="/research/:jobId" element={<ResearchDetailPage />} />
        <Route path="/research-project/:projectId" element={<ResearchProjectPage />} />
        <Route path="/competitors" element={<CompetitorsPage />} />
        <Route path="/trends" element={<TrendsPage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
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
