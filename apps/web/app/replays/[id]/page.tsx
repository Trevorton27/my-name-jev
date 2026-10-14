"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { ReplayRun } from "@/lib/types";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-800 text-gray-400 border-gray-700",
  running: "bg-blue-900/50 text-blue-400 border-blue-800",
  completed: "bg-green-900/50 text-green-400 border-green-800",
  failed: "bg-red-900/50 text-red-400 border-red-800",
};

export default function ReplayDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const { data, isLoading, error } = useQuery<ReplayRun>({
    queryKey: ["replay", id],
    queryFn: () => fetchAPI<ReplayRun>(`/v1/replays/${id}`),
    refetchInterval: (query) => {
      const run = query.state.data;
      return run && run.status === "running" ? 3000 : false;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400">Loading replay...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <p className="text-red-400">
          Failed to load replay: {(error as Error).message}
        </p>
      </div>
    );
  }

  if (!data) {
    return <div className="text-gray-400">Replay not found.</div>;
  }

  const progress =
    data.total_decisions > 0
      ? Math.round((data.processed_decisions / data.total_decisions) * 100)
      : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/replays"
          className="text-gray-400 hover:text-gray-200 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold text-white">{data.name}</h1>
        <span
          className={`inline-block px-2.5 py-1 text-xs font-medium rounded border ${
            STATUS_COLORS[data.status] || STATUS_COLORS.pending
          }`}
        >
          {data.status}
        </span>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-4">Progress</h2>
        <div className="space-y-3">
          <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">
              {data.processed_decisions} / {data.total_decisions} decisions
            </span>
            <span className="text-gray-300 font-medium">{progress}%</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Total" value={data.total_decisions} />
        <StatCard label="Matches" value={data.matches} color="text-green-400" />
        <StatCard
          label="Mismatches"
          value={data.mismatches}
          color="text-red-400"
        />
        <StatCard
          label="Errors"
          value={data.errors}
          color="text-yellow-400"
        />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-3">Details</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wider block mb-0.5">
              Replay ID
            </span>
            <span className="text-xs font-mono text-gray-300">{data.id}</span>
          </div>
          <div>
            <span className="text-xs text-gray-500 uppercase tracking-wider block mb-0.5">
              Created At
            </span>
            <span className="text-sm text-gray-300">
              {new Date(data.created_at).toLocaleString()}
            </span>
          </div>
          {data.completed_at && (
            <div>
              <span className="text-xs text-gray-500 uppercase tracking-wider block mb-0.5">
                Completed At
              </span>
              <span className="text-sm text-gray-300">
                {new Date(data.completed_at).toLocaleString()}
              </span>
            </div>
          )}
          {data.total_decisions > 0 && (
            <div>
              <span className="text-xs text-gray-500 uppercase tracking-wider block mb-0.5">
                Match Rate
              </span>
              <span className="text-sm text-gray-300">
                {data.processed_decisions > 0
                  ? (
                      (data.matches / data.processed_decisions) *
                      100
                    ).toFixed(1)
                  : "0"}
                %
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
        {label}
      </p>
      <p className={`text-2xl font-semibold mt-1 ${color || "text-white"}`}>
        {value}
      </p>
    </div>
  );
}
