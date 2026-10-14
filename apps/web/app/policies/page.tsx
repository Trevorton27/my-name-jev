"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { Policy } from "@/lib/types";
import Link from "next/link";

export default function PoliciesPage() {
  const { data, isLoading, error } = useQuery<Policy[]>({
    queryKey: ["policies"],
    queryFn: () => fetchAPI<Policy[]>("/v1/policies"),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Policies</h1>

      {isLoading && (
        <div className="flex items-center justify-center h-40">
          <p className="text-gray-400">Loading policies...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
          <p className="text-red-400">
            Failed to load policies: {(error as Error).message}
          </p>
        </div>
      )}

      {data && data.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-400">No policies defined yet.</p>
        </div>
      )}

      {data && data.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
                <th className="text-left px-4 py-3 font-medium">Name</th>
                <th className="text-left px-4 py-3 font-medium">
                  Action Types
                </th>
                <th className="text-left px-4 py-3 font-medium">
                  Active Version
                </th>
                <th className="text-left px-4 py-3 font-medium">
                  Created At
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {data.map((policy) => (
                <tr
                  key={policy.id}
                  className="hover:bg-gray-800/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link
                      href={`/policies/${policy.id}`}
                      className="text-indigo-400 hover:text-indigo-300 font-medium"
                    >
                      {policy.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {policy.action_types.map((at) => (
                        <span
                          key={at}
                          className="inline-block px-2 py-0.5 text-xs rounded bg-gray-800 text-gray-400 border border-gray-700"
                        >
                          {at}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-300 font-mono text-xs">
                    v{policy.active_version}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(policy.created_at).toLocaleString()}
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
