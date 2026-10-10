"use client";

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import type { AuthUser } from "@/lib/auth";
import {
  AuthenticationRequiredError,
  getCurrentUser,
  logout as logoutRequest,
} from "@/lib/auth";

type AuthContextValue = {
  user: AuthUser | null;
  authenticated: boolean;
  loading: boolean;
  refreshUser: () => Promise<boolean>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const mounted = useRef(false);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser();
      if (mounted.current) setUser(currentUser);
      return true;
    } catch (error) {
      if (mounted.current) setUser(null);
      if (error instanceof AuthenticationRequiredError) return false;
      throw error;
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, []);

  const signOut = useCallback(async () => {
    try {
      await logoutRequest();
    } finally {
      if (mounted.current) setUser(null);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    const onUnauthorized = () => setUser(null);
    window.addEventListener("bankwise:unauthorized", onUnauthorized);
    let active = true;
    void getCurrentUser()
      .then((currentUser) => {
        if (active) setUser(currentUser);
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
      mounted.current = false;
      window.removeEventListener("bankwise:unauthorized", onUnauthorized);
    };
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, authenticated: user !== null, loading, refreshUser, signOut }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
