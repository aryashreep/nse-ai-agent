import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "NSE Agentic Research Platform",
  description: "Institutional-grade momentum analysis and research for Indian equities",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="app-container">
          <header className="header">
            <Link href="/" className="logo-section">
              <div className="logo-badge">N</div>
              <span className="logo-text">NSE Agentic Research</span>
            </Link>
            <nav className="nav-links">
              <Link href="/" className="nav-link">Dashboard</Link>
              <Link href="/screen" className="nav-link">Screener</Link>
              <Link href="/sector" className="nav-link">Sector Rotation</Link>
              <Link href="/portfolio" className="nav-link">Portfolio Review</Link>
            </nav>
          </header>
          
          <main className="main-content">
            {children}
          </main>
          
          <footer className="footer">
            <p>&copy; {new Date().getFullYear()} NSE Agentic Research Platform. Built in the open. For educational purposes only.</p>
          </footer>
        </div>
      </body>
    </html>
  );
}
