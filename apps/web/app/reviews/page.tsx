"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAPI } from "@/lib/api";
import { Review } from "@/lib/types";

export default function ReviewsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery<Review[]>({
    queryKey: ["reviews"],
    queryFn: () => fetchAPI<Review[]>("/v1/reviews?status=pending"),
  });

  const mutation = useMutation({
    mutationFn: ({
      id,
      action,
      reason,
    }: {
      id: string;
      action: "approve" | "reject";
      reason?: string;
    }) =>
      fetchAPI(`/v1/reviews/${id}/${action}`, {
        method: "POST",
        body: JSON.stringify({ reason: reason || "" }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews"] });
    },
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Review Queue</h1>

      {isLoading && (
        <div className="flex items-center justify-center h-40">
          <p className="text-gray-400">Loading reviews...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
          <p className="text-red-400">
            Failed to load reviews: {(error as Error).message}
          </p>
        </div>
      )}

      {data && data.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center">
          <p className="text-gray-400">No pending reviews.</p>
        </div>
      )}

      {data && data.length > 0 && (
        <div className="space-y-3">
          {data.map((review) => (
            <div
              key={review.id}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-center justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono text-gray-400">
                    {review.id.slice(0, 8)}...
                  </span>
                  <span className="inline-block px-2 py-0.5 text-xs font-medium rounded border bg-yellow-900/50 text-yellow-400 border-yellow-800">
                    {review.status}
                  </span>
                </div>
                <p className="text-sm text-gray-300">
                  Decision:{" "}
                  <span className="font-mono text-xs text-indigo-400">
                    {review.decision_id.slice(0, 12)}...
                  </span>
                </p>
                <p className="text-xs text-gray-500">
                  Created: {new Date(review.created_at).toLocaleString()}
                </p>
                {review.reviewer && (
                  <p className="text-xs text-gray-500">
                    Reviewer: {review.reviewer}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() =>
                    mutation.mutate({ id: review.id, action: "approve" })
                  }
                  disabled={mutation.isPending}
                  className="px-3 py-1.5 text-xs font-medium rounded bg-green-900/50 text-green-400 border border-green-800 hover:bg-green-900 transition-colors disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  onClick={() =>
                    mutation.mutate({ id: review.id, action: "reject" })
                  }
                  disabled={mutation.isPending}
                  className="px-3 py-1.5 text-xs font-medium rounded bg-red-900/50 text-red-400 border border-red-800 hover:bg-red-900 transition-colors disabled:opacity-50"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
