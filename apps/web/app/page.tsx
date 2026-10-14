"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { AnalyticsOverview } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery<AnalyticsOverview>({
    queryKey: ["analytics-overview"],
    queryFn: () => fetchAPI<AnalyticsOverview>("/v1/analytics/overview"),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400">Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <p className="text-red-400">
          Failed to load dashboard: {(error as Error).message}
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-gray-400">No data available.</div>
    );
  }

  const chartData = Object.entries(data.disposition_breakdown).map(
    ([name, value]) => ({ name, value })
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Decisions" value={data.total_decisions} />
        <StatCard label="Decisions Today" value={data.decisions_today} />
        <StatCard label="Pending Reviews" value={data.pending_reviews} />
        <StatCard
          label="Avg Latency"
          value={`${data.avg_latency_ms.toFixed(1)}ms`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="text-sm font-medium text-gray-400 mb-4">
            Disposition Breakdown
          </h2>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "6px",
                    color: "#f3f4f6",
                  }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-sm">No disposition data yet.</p>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="text-sm font-medium text-gray-400 mb-4">
            Latency Stats
          </h2>
          <div className="space-y-3">
            <LatencyStat label="Average" value={data.avg_latency_ms} />
            <LatencyStat label="p95" value={data.p95_latency_ms} />
            <LatencyStat label="p99" value={data.p99_latency_ms} />
          </div>
          <div className="mt-6 pt-4 border-t border-gray-800">
            <p className="text-xs text-gray-500">
              Decisions this week:{" "}
              <span className="text-gray-300">
                {data.decisions_this_week}
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
        {label}
      </p>
      <p className="text-2xl font-semibold text-white mt-1">{value}</p>
    </div>
  );
}

function LatencyStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-400">{label}</span>
      <span className="text-sm font-mono text-white">
        {value.toFixed(1)}ms
      </span>
    </div>
  );
}
