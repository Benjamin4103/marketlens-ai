import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Compass } from "lucide-react";
import { useAuth } from "@/stores/auth";

export function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password, fullName);
      }
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-ink px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-lg bg-verified-dim text-verified">
            <Compass size={22} strokeWidth={2} />
          </div>
          <h1 className="font-display text-2xl font-semibold text-paper">MarketLens AI</h1>
          <p className="mt-1 text-sm text-muted">Evidence-backed market intelligence</p>
        </div>

        <div className="rounded-xl border border-line bg-surface p-6">
          <div className="mb-5 flex rounded-md bg-surface-raised p-1 text-sm">
            <button
              onClick={() => setMode("login")}
              className={`flex-1 rounded px-3 py-1.5 transition-colors ${
                mode === "login" ? "bg-ink text-paper" : "text-muted"
              }`}
            >
              Sign in
            </button>
            <button
              onClick={() => setMode("register")}
              className={`flex-1 rounded px-3 py-1.5 transition-colors ${
                mode === "register" ? "bg-ink text-paper" : "text-muted"
              }`}
            >
              Create account
            </button>
          </div>

          <form onSubmit={submit} className="space-y-3">
            {mode === "register" && (
              <input
                type="text"
                placeholder="Full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-md border border-line bg-ink px-3 py-2 text-sm text-paper placeholder:text-faint focus:border-verified focus:outline-none"
              />
            )}
            <input
              type="email"
              required
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-line bg-ink px-3 py-2 text-sm text-paper placeholder:text-faint focus:border-verified focus:outline-none"
            />
            <input
              type="password"
              required
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-line bg-ink px-3 py-2 text-sm text-paper placeholder:text-faint focus:border-verified focus:outline-none"
            />

            {error && <p className="text-xs text-alert">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-verified py-2 text-sm font-medium text-ink transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
