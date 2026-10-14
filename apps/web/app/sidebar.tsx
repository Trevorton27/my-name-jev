"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  GitBranch,
  ClipboardCheck,
  Shield,
  FlaskConical,
  Play,
  ScrollText,
  Plug,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/decisions", label: "Decisions", icon: GitBranch },
  { href: "/reviews", label: "Reviews", icon: ClipboardCheck },
  { href: "/policies", label: "Policies", icon: Shield },
  { href: "/calibration", label: "Calibration", icon: FlaskConical },
  { href: "/replays", label: "Replays", icon: Play },
  { href: "/audit", label: "Audit", icon: ScrollText },
  { href: "/integrations", label: "Integrations", icon: Plug },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
      <div className="px-4 py-5 border-b border-gray-800">
        <h1 className="text-lg font-bold tracking-tight text-white">
          jevOps Console
        </h1>
      </div>
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? "bg-gray-800 text-white"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-gray-800 text-xs text-gray-500">
        jevOps v0.1.0
      </div>
    </aside>
  );
}
