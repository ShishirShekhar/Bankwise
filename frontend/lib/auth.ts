"use client";

import {
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
  type UserCredential,
} from "firebase/auth";

import { ApiError, apiFetch } from "@/lib/api-client";
import { getFirebaseAuth } from "@/lib/firebase";

export type AuthUser = {
  uid: string;
  email: string | null;
  name: string | null;
};

export class AuthenticationRequiredError extends Error {
  constructor() {
    super("Authentication required");
    this.name = "AuthenticationRequiredError";
  }
}

function firebaseErrorCode(error: unknown): string | null {
  if (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string"
  ) {
    return error.code;
  }
  return null;
}

function friendlyFirebaseError(error: unknown): Error {
  const code = firebaseErrorCode(error);
  if (!code?.startsWith("auth/")) {
    return error instanceof Error ? error : new Error("Sign-in could not be completed.");
  }

  const messages: Record<string, string> = {
    "auth/invalid-email": "Enter a valid email address.",
    "auth/weak-password": "Choose a stronger password.",
    "auth/email-already-in-use": "An account with this email already exists.",
    "auth/invalid-credential": "Email or password is incorrect.",
    "auth/user-disabled": "This account has been disabled.",
    "auth/too-many-requests": "Too many attempts. Please wait and try again.",
    "auth/account-exists-with-different-credential":
      "An account already exists with this email. Sign in using its original method first.",
    "auth/unauthorized-domain":
      "This site is not authorized for Firebase sign-in. Add its domain in Firebase Authentication settings.",
    "auth/operation-not-allowed":
      "This sign-in method is disabled for the Firebase project.",
    "auth/invalid-api-key": "Firebase web configuration is invalid.",
    "auth/app-not-authorized": "This app is not authorized for Firebase sign-in.",
    "auth/invalid-oauth-client-id":
      "Google sign-in is misconfigured in Firebase Authentication settings.",
    "auth/popup-closed-by-user": "Google sign-in was closed before it finished.",
    "auth/popup-blocked": "Your browser blocked the sign-in popup. Allow popups and try again.",
    "auth/network-request-failed": "Network error. Check your connection and try again.",
  };

  return new Error(messages[code] ?? `Sign-in failed (${code}). Please try again.`);
}

async function establishServerSession(credential: UserCredential): Promise<void> {
  try {
    const idToken = await credential.user.getIdToken();
    await apiFetch("/api/auth/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idToken }),
    });
  } finally {
    await firebaseSignOut(getFirebaseAuth());
  }
}

async function authenticate(operation: () => Promise<UserCredential>): Promise<void> {
  try {
    await establishServerSession(await operation());
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw friendlyFirebaseError(error);
  }
}

export function signInWithEmail(email: string, password: string): Promise<void> {
  return authenticate(() =>
    signInWithEmailAndPassword(getFirebaseAuth(), email, password),
  );
}

export function signUpWithEmail(email: string, password: string): Promise<void> {
  return authenticate(() =>
    createUserWithEmailAndPassword(getFirebaseAuth(), email, password),
  );
}

export function signInWithGoogle(): Promise<void> {
  const provider = new GoogleAuthProvider();
  return authenticate(() => signInWithPopup(getFirebaseAuth(), provider));
}

export async function getCurrentUser(): Promise<AuthUser> {
  try {
    const response = await apiFetch("/api/auth/me");
    const user = (await response.json()) as AuthUser;
    return user;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      throw new AuthenticationRequiredError();
    }
    throw error;
  }
}

export async function logout(): Promise<void> {
  try {
    await apiFetch("/api/auth/logout", { method: "POST" });
  } finally {
    await firebaseSignOut(getFirebaseAuth());
  }
}
