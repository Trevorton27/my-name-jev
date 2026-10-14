"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { Policy } from "@/lib/types";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

export default function PolicyDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const { data, isLoading, error } = useQuery<Policy>({
    queryKey: ["policy", id],
    queryFn: () => fetchAPI<Policy>(`/v1/policies/${id}`),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400">Loading policy...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <p className="text-red-400">
          Failed to load policy: {(error as Error).message}
        </p>
      </div>
    );
  }

  if (!data) {
    return <div className="text-gray-400">Policy not found.</div>;
  }

  const activeVersion = data.versions?.find(
    (v) => v.version === data.active_version
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/policies"
          className="text-gray-400 hover:text-gray-200 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold text-white">{data.name}</h1>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 space-y-3">
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wider block mb-0.5">
            Description
          </span>
          <p className="text-sm text-gray-300">{data.description}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wider block mb-0.5">
              ID
            </span>
            <span className="text-xs font-mono text-gray-300">{data.id}</span>
          </div>
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wider block mb-0.5">
              Active Version
            </span>
            <span className="text-sm text-gray-300">
              v{data.active_version}
            </span>
          </div>
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wider block mb-0.5">
              Action Types
            </span>
            <div className="flex flex-wrap gap-1 mt-0.5">
              {data.action_types.map((at) => (
                <span
                  key={at}
                  className="inline-block px-2 py-0.5 text-xs rounded bg-gray-800 text-gray-400 border border-gray-700"
                >
                  {at}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {activeVersion && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <h2 className="text-sm font-medium text-gray-400 mb-3">
            Active Policy Content (v{activeVersion.version})
          </h2>
          <pre className="bg-gray-950 border border-gray-800 rounded p-4 text-xs text-gray-300 overflow-auto max-h-96 font-mono whitespace-pre-wrap">
            {activeVersion.content}
          </pre>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-3">
          Version History
        </h2>
        {(!data.versions || data.versions.length === 0) && (
          <p className="text-gray-500 text-sm">No versions available.</p>
        )}
        {data.versions && data.versions.length > 0 && (
          <div className="space-y-2">
            {data.versions
              .sort((a, b) => b.version - a.version)
              .map((version) => (
                <div
                  key={version.id}
                  className={`flex items-center justify-between p-3 rounded border ${
                    version.version === data.active_version
                      ? "bg-indigo-900/20 border-indigo-800"
                      : "bg-gray-950 border-gray-800"
                  }`}
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-mono text-gray-200">
                        v{version.version}
                      </span>
                      {version.version === data.active_version && (
                        <span className="px-1.5 py-0.5 text-xs rounded bg-indigo-900/50 text-indigo-400 border border-indigo-800">
                          active
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500">
                      {version.changelog || "No changelog"}
                    </p>
                  </div>
                  <span className="text-xs text-gray-600">
                    {new Date(version.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
