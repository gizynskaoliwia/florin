import "./globals.css";
import { Inter, Playfair_Display, JetBrains_Mono } from "next/font/google";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const playfair = Playfair_Display({ subsets: ["latin"], variable: "--font-serif" });
const jbMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata = {
  title: "Florin",
  description: "Rise above your finances",
};

function Sidebar() {
  const navItems = [
    { name: "Dashboard", href: "/", icon: "✦" },
    { name: "Income", href: "/income", icon: "💰" },
    { name: "Expenses", href: "/expenses", icon: "🧾" },
    { name: "Shared Goals", href: "/shared-goals", icon: "🎯" },
  ];

  return (
    <div className="w-[220px] h-screen bg-[var(--color-surface)] border-r border-[var(--color-border)] flex flex-col">
      <div className="h-[64px] flex items-center px-4">
        <span className="text-[var(--color-primary)] font-bold text-xl mr-2">✦</span>
        <span className="font-serif font-bold text-xl text-[var(--color-text)]">Florin</span>
      </div>
      <div className="h-[1px] bg-[var(--color-border)] w-full mb-4"></div>
      
      <div className="flex-1 px-3">
        <div className="text-[var(--color-text-faint)] text-xs font-bold mb-2 px-3 tracking-wider">MAIN</div>
        {navItems.map((item) => (
          <Link key={item.name} href={item.href} className="flex items-center px-3 py-2 mb-1 rounded-lg hover:bg-[var(--color-surface-2)] group text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
            <span className="mr-3 opacity-70 group-hover:opacity-100">{item.icon}</span>
            <span className="text-sm font-medium">{item.name}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${playfair.variable} ${jbMono.variable} antialiased flex bg-[var(--color-app-bg)] h-screen overflow-hidden`}>
        <Sidebar />
        <main className="flex-1 h-full overflow-y-auto p-6">
          <div className="max-w-5xl mx-auto">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
