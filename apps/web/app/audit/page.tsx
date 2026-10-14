"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { AuditEvent } from "@/lib/types";

export default function AuditPage() {
  const { data, isLoading, error } = useQuery<AuditEvent[]>({
    queryKey: ["audit"],
    queryFn: () => fetchAPI<AuditEvent[]>("/v1/audit"),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Audit Log</h1>

      {isLoading && (
        <div className="flex items-center justify-center h-40">
          <p className="text-gray-400">Loading audit events...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
          <p className="text-red-400">
            Failed to load audit log: {(error as Error).message}
          </p>
        </div>
      )}

      {data && data.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-400">No audit events recorded.</p>
        </div>
      )}

      {data && data.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
                <th className="text-left px-4 py-3 font-medium">Timestamp</th>
                <th className="text-left px-4 py-3 font-medium">Event Type</th>
                <th className="text-left px-4 py-3 font-medium">Actor</th>
                <th className="text-left px-4 py-3 font-medium">Resource</th>
                <th className="text-left px-4 py-3 font-medium">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {data.map((event) => (
                <tr
                  key={event.id}
                  className="hover:bg-gray-800/50 transition-colors"
                >
                  <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                    {new Date(event.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-block px-2 py-0.5 text-xs font-medium rounded bg-gray-800 text-gray-300 border border-gray-700">
                      {event.event_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-300 text-xs font-mono">
                    {event.actor}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    <span className="text-gray-500">{event.resource_type}/</span>
                    <span className="font-mono">
                      {event.resource_id.slice(0, 8)}...
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs max-w-xs truncate">
                    {JSON.stringify(event.details)}
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
