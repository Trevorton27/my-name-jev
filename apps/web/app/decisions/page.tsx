"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { Decision } from "@/lib/types";
import Link from "next/link";
import { useState } from "react";

const DISPOSITION_COLORS: Record<string, string> = {
  allow: "bg-green-900/50 text-green-400 border-green-800",
  deny: "bg-red-900/50 text-red-400 border-red-800",
  escalate: "bg-yellow-900/50 text-yellow-400 border-yellow-800",
  review: "bg-blue-900/50 text-blue-400 border-blue-800",
};

export default function DecisionsPage() {
  const [dispositionFilter, setDispositionFilter] = useState<string>("all");

  const { data, isLoading, error } = useQuery<Decision[]>({
    queryKey: ["decisions", dispositionFilter],
    queryFn: () => {
      const params =
        dispositionFilter !== "all"
          ? `?disposition=${dispositionFilter}`
          : "";
      return fetchAPI<Decision[]>(`/v1/decisions${params}`);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Decisions</h1>
        <select
          value={dispositionFilter}
          onChange={(e) => setDispositionFilter(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="all">All Dispositions</option>
          <option value="allow">Allow</option>
          <option value="deny">Deny</option>
          <option value="escalate">Escalate</option>
          <option value="review">Review</option>
        </select>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-40">
          <p className="text-gray-400">Loading decisions...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
          <p className="text-red-400">
            Failed to load decisions: {(error as Error).message}
          </p>
        </div>
      )}

      {data && data.length === 0 && (
        <div className="text-gray-400 text-center py-12">
          No decisions found.
        </div>
      )}

      {data && data.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
                <th className="text-left px-4 py-3 font-medium">ID</th>
                <th className="text-left px-4 py-3 font-medium">Action Type</th>
                <th className="text-left px-4 py-3 font-medium">Disposition</th>
                <th className="text-left px-4 py-3 font-medium">Agent</th>
                <th className="text-left px-4 py-3 font-medium">Environment</th>
                <th className="text-left px-4 py-3 font-medium">Created At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {data.map((decision) => (
                <tr
                  key={decision.id}
                  className="hover:bg-gray-800/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/decisions/${decision.id}`}
                      className="text-indigo-400 hover:text-indigo-300 font-mono text-xs"
                    >
                      {decision.id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {decision.action_type}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 text-xs font-medium rounded border ${
                        DISPOSITION_COLORS[decision.disposition] ||
                        "bg-gray-800 text-gray-400 border-gray-700"
                      }`}
                    >
                      {decision.disposition}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-300 font-mono text-xs">
                    {decision.agent}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {decision.environment}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(decision.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
