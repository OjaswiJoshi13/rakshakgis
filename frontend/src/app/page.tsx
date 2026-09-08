"use client";

import LoginPage from "./login/page";

/**
 * Root Application Entry Route (/)
 *
 * Public access displays the authoritative login gateway.
 * Authenticated sessions are automatically redirected to /dashboard.
 */
export default function HomePage() {
  return <LoginPage />;
}
