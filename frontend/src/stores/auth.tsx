import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { api, setToken, clearToken } from "@/lib/api";
import type { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const cached = localStorage.getItem("mlens_user");
    return cached ? JSON.parse(cached) : null;
  });

  const persistUser = (u: User) => {
    setUser(u);
    localStorage.setItem("mlens_user", JSON.stringify(u));
  };

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password);
    setToken(access_token);
    // Minimal user object; backend doesn't expose a "me" endpoint yet, so we
    // store what we have locally after a successful login.
    persistUser({ id: "", email, full_name: "", is_active: true });
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    const u = await api.register(email, password, fullName);
    const { access_token } = await api.login(email, password);
    setToken(access_token);
    persistUser(u);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    localStorage.removeItem("mlens_user");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
