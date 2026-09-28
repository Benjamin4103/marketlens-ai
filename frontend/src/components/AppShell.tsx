import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  Users,
  TrendingUp,
  FileStack,
  FileText,
  Settings,
  Compass,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/stores/auth";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/research", label: "New Research", icon: Search },
  { to: "/competitors", label: "Competitors", icon: Users },
  { to: "/trends", label: "Trends", icon: TrendingUp },
  { to: "/sources", label: "Sources", icon: FileStack },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex h-screen bg-ink text-paper">
      <aside className="flex w-60 shrink-0 flex-col border-r border-line bg-surface">
        <div className="flex items-center gap-2 px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-verified-dim text-verified">
            <Compass size={18} strokeWidth={2} />
          </div>
          <div>
            <div className="font-display text-[15px] font-semibold leading-tight">MarketLens</div>
            <div className="font-mono text-[10px] uppercase tracking-wider text-muted">AI Intelligence</div>
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 px-3">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-surface-raised text-paper"
                    : "text-muted hover:bg-surface-raised/60 hover:text-paper"
                }`
              }
            >
              <Icon size={16} strokeWidth={2} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-line px-3 py-3">
          <div className="mb-2 px-3 font-mono text-[11px] text-muted truncate">{user?.email}</div>
          <button
            onClick={() => {
              logout();
              navigate("/login");
            }}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-muted transition-colors hover:bg-surface-raised/60 hover:text-alert"
          >
            <LogOut size={16} strokeWidth={2} />
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
