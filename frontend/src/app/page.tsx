"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { LogIn, Hotel, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { apiUrl } from "@/lib/api";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [businessName, setBusinessName] = useState("Hotel PMS");

  useEffect(() => {
    void fetch(apiUrl("/public/settings"))
      .then((response) => response.json())
      .then((settings: { business_name?: string }) => {
        if (settings.business_name) setBusinessName(settings.business_name);
      })
      .catch(() => undefined);
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("username", username);
      formData.append("password", password);

      const response = await fetch(apiUrl("/token"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Invalid credentials");
      }

      const data = await response.json();
      localStorage.setItem("token", data.access_token);
      
      // Navigate to dashboard
      window.location.href = "/dashboard";
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center bg-black overflow-hidden">
      {/* Magic Background Effect */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,#1a1a1a,black)]" />
        <div className="absolute top-0 left-0 w-full h-full opacity-20 bg-[grid-white]/[0.05] [mask-image:radial-gradient(ellipse_at_center,black,transparent)]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="relative z-10 w-full max-w-md p-8 bg-zinc-900/50 border border-zinc-800 rounded-2xl backdrop-blur-xl"
      >
        <div className="flex flex-col items-center mb-8">
          <motion.div
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ 
              repeat: Infinity, 
              repeatType: "reverse", 
              duration: 2 
            }}
            className="w-16 h-16 bg-emerald-500/10 flex items-center justify-center rounded-full mb-4 border border-emerald-500/20"
          >
            <Hotel className="w-8 h-8 text-emerald-500" />
          </motion.div>
          <h1 className="text-3xl font-bold text-white tracking-tight">{businessName}</h1>
          <p className="text-zinc-400 text-sm mt-2 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            Secure Enterprise Management
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          {error && (
            <p className="text-red-400 text-sm bg-red-400/10 p-3 rounded-lg border border-red-400/20 text-center animate-pulse">
              {error}
            </p>
          )}
          <div>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all placeholder:text-zinc-600"
              required
            />
          </div>
          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full px-4 py-3 bg-zinc-950 border border-zinc-800 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all placeholder:text-zinc-600"
              required
            />
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            disabled={loading}
            className={cn(
              "w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors",
              loading && "opacity-70 cursor-not-allowed"
            )}
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <LogIn className="w-5 h-5" />
                Access Dashboard
              </>
            )}
          </motion.button>
        </form>

        <div className="mt-8 pt-6 border-t border-zinc-800/50 text-center">
          <p className="text-zinc-500 text-xs">
            {businessName}
          </p>
        </div>
      </motion.div>

      {/* Animated Glows */}
      <div className="absolute top-1/4 -left-20 w-80 h-80 bg-emerald-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 -right-20 w-80 h-80 bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />
    </div>
  );
}
