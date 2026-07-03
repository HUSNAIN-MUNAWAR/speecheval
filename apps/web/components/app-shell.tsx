"use client";
import { useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { TopNav } from "@/components/top-nav";
export function AppShell({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const [compact, setCompact] = useState(false);
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[auto_1fr]">
      <Sidebar compact={compact} onCompactChange={setCompact} />
      <main className="min-w-0">
        <TopNav />
        <div className="mx-auto max-w-[1600px] px-4 py-5 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
