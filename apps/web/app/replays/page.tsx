"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { ReplayRun } from "@/lib/types";
import Link from "next/link";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-800 text-gray-400 border-gray-700",
  running: "bg-blue-900/50 text-blue-400 border-blue-800",
  completed: "bg-green-900/50 text-green-400 border-green-800",
  failed: "bg-red-900/50 text-red-400 border-red-800",
};

export default function ReplaysPage() {
  const { data, isLoading, error } = useQuery<ReplayRun[]>({
    queryKey: ["replays"],
    queryFn: () => fetchAPI<ReplayRun[]>("/v1/replays"),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Replays</h1>

      {isLoading && (
        <div className="flex items-center justify-center h-40">
          <p className="text-gray-400">Loading replays...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
          <p className="text-red-400">
            Failed to load replays: {(error as Error).message}
          </p>
        </div>
      )}

      {data && data.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-400">No replay runs found.</p>
        </div>
      )}

      {data && data.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
                <th className="text-left px-4 py-3 font-medium">Name</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Progress</th>
                <th className="text-left px-4 py-3 font-medium">Matches</th>
                <th className="text-left px-4 py-3 font-medium">Mismatches</th>
                <th className="text-left px-4 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {data.map((run) => {
                const progress =
                  run.total_decisions > 0
                    ? Math.round(
                        (run.processed_decisions / run.total_decisions) * 100
                      )
                    : 0;
                return (
                  <tr
                    key={run.id}
                    className="hover:bg-gray-800/50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/replays/${run.id}`}
                        className="text-indigo-400 hover:text-indigo-300"
                      >
                        {run.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 text-xs font-medium rounded border ${
                          STATUS_COLORS[run.status] || STATUS_COLORS.pending
                        }`}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full transition-all"
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">
                          {progress}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-green-400 text-xs font-mono">
                      {run.matches}
                    </td>
                    <td className="px-4 py-3 text-red-400 text-xs font-mono">
                      {run.mismatches}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
