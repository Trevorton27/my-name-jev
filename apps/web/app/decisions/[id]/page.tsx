"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { Decision } from "@/lib/types";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

const DISPOSITION_COLORS: Record<string, string> = {
  allow: "bg-green-900/50 text-green-400 border-green-800",
  deny: "bg-red-900/50 text-red-400 border-red-800",
  escalate: "bg-yellow-900/50 text-yellow-400 border-yellow-800",
  review: "bg-blue-900/50 text-blue-400 border-blue-800",
};

export default function DecisionDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const { data, isLoading, error } = useQuery<Decision>({
    queryKey: ["decision", id],
    queryFn: () => fetchAPI<Decision>(`/v1/decisions/${id}`),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-400">Loading decision...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
        <p className="text-red-400">
          Failed to load decision: {(error as Error).message}
        </p>
      </div>
    );
  }

  if (!data) {
    return <div className="text-gray-400">Decision not found.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/decisions"
          className="text-gray-400 hover:text-gray-200 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <h1 className="text-2xl font-bold text-white">Decision Detail</h1>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="ID" value={data.id} mono />
          <Field label="Action Type" value={data.action_type} />
          <Field label="Agent" value={data.agent} mono />
          <Field label="Environment" value={data.environment} />
          <Field label="Latency" value={`${data.latency_ms}ms`} />
          <Field
            label="Created At"
            value={new Date(data.created_at).toLocaleString()}
          />
        </div>
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wider block mb-1">
            Disposition
          </span>
          <span
            className={`inline-block px-2.5 py-1 text-xs font-medium rounded border ${
              DISPOSITION_COLORS[data.disposition] ||
              "bg-gray-800 text-gray-400 border-gray-700"
            }`}
          >
            {data.disposition}
          </span>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-3">Input</h2>
        <pre className="bg-gray-950 border border-gray-800 rounded p-3 text-xs text-gray-300 overflow-auto max-h-60">
          {JSON.stringify(data.input, null, 2)}
        </pre>
      </div>

      {data.output && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <h2 className="text-sm font-medium text-gray-400 mb-3">Output</h2>
          <pre className="bg-gray-950 border border-gray-800 rounded p-3 text-xs text-gray-300 overflow-auto max-h-60">
            {JSON.stringify(data.output, null, 2)}
          </pre>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-3">
          Judgments ({data.judgments?.length || 0})
        </h2>
        {(!data.judgments || data.judgments.length === 0) && (
          <p className="text-gray-500 text-sm">No judgments recorded.</p>
        )}
        {data.judgments && data.judgments.length > 0 && (
          <div className="space-y-3">
            {data.judgments.map((j) => (
              <div
                key={j.id}
                className="bg-gray-950 border border-gray-800 rounded p-3 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-200">
                    {j.judge_name}
                  </span>
                  <span className="text-xs text-gray-500">
                    Confidence: {(j.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-gray-400">{j.reasoning}</p>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">Disposition:</span>
                  <span
                    className={`inline-block px-2 py-0.5 text-xs rounded border ${
                      DISPOSITION_COLORS[j.disposition] ||
                      "bg-gray-800 text-gray-400 border-gray-700"
                    }`}
                  >
                    {j.disposition}
                  </span>
                </div>
                <pre className="bg-gray-900 border border-gray-800 rounded p-2 text-xs text-gray-300 overflow-auto">
                  {JSON.stringify(j.value, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-3">
          Policy Trace
        </h2>
        {(!data.policy_trace || data.policy_trace.length === 0) && (
          <p className="text-gray-500 text-sm">No policy trace available.</p>
        )}
        {data.policy_trace && data.policy_trace.length > 0 && (
          <ol className="space-y-1">
            {data.policy_trace.map((step, i) => (
              <li
                key={i}
                className="text-xs font-mono text-gray-300 flex items-center gap-2"
              >
                <span className="text-gray-600">{i + 1}.</span>
                {step}
              </li>
            ))}
          </ol>
        )}
      </div>

      {data.outcome && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
          <h2 className="text-sm font-medium text-gray-400 mb-3">Outcome</h2>
          <pre className="bg-gray-950 border border-gray-800 rounded p-3 text-xs text-gray-300 overflow-auto max-h-60">
            {JSON.stringify(data.outcome, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <span className="text-xs text-gray-500 uppercase tracking-wider block mb-0.5">
        {label}
      </span>
      <span
        className={`text-sm text-gray-200 ${mono ? "font-mono text-xs" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}
