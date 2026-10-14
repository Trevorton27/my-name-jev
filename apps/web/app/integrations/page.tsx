"use client";

import { useState } from "react";
import { Eye, EyeOff, Copy, Plus, Trash2 } from "lucide-react";

export default function IntegrationsPage() {
  const [showApiKey, setShowApiKey] = useState(false);
  const [webhooks, setWebhooks] = useState<
    { id: string; url: string; events: string[] }[]
  >([]);
  const [newWebhookUrl, setNewWebhookUrl] = useState("");
  const [newWebhookEvents, setNewWebhookEvents] = useState("");

  const apiKey = process.env.NEXT_PUBLIC_API_KEY || "not-configured";

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
  };

  const handleAddWebhook = () => {
    if (!newWebhookUrl.trim()) return;
    const events = newWebhookEvents
      .split(",")
      .map((e) => e.trim())
      .filter(Boolean);
    setWebhooks((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        url: newWebhookUrl.trim(),
        events: events.length > 0 ? events : ["*"],
      },
    ]);
    setNewWebhookUrl("");
    setNewWebhookEvents("");
  };

  const handleRemoveWebhook = (id: string) => {
    setWebhooks((prev) => prev.filter((w) => w.id !== id));
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Integrations</h1>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-4">API Key</h2>
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-gray-950 border border-gray-800 rounded px-3 py-2 font-mono text-sm text-gray-300">
            {showApiKey ? apiKey : "••••••••••••••••••••••••••••••••"}
          </div>
          <button
            onClick={() => setShowApiKey(!showApiKey)}
            className="p-2 text-gray-400 hover:text-gray-200 transition-colors"
            title={showApiKey ? "Hide" : "Show"}
          >
            {showApiKey ? (
              <EyeOff className="w-4 h-4" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
          </button>
          <button
            onClick={handleCopyKey}
            className="p-2 text-gray-400 hover:text-gray-200 transition-colors"
            title="Copy"
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          Set via NEXT_PUBLIC_API_KEY environment variable. Used in the X-API-Key
          header for all API requests.
        </p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-4">
          Webhook Configuration
        </h2>

        <div className="space-y-3 mb-4">
          <div className="flex gap-3">
            <input
              type="url"
              value={newWebhookUrl}
              onChange={(e) => setNewWebhookUrl(e.target.value)}
              placeholder="https://example.com/webhook"
              className="flex-1 bg-gray-950 border border-gray-800 rounded px-3 py-2 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <input
              type="text"
              value={newWebhookEvents}
              onChange={(e) => setNewWebhookEvents(e.target.value)}
              placeholder="Events (comma-separated, or * for all)"
              className="w-64 bg-gray-950 border border-gray-800 rounded px-3 py-2 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <button
              onClick={handleAddWebhook}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded bg-indigo-600 text-white hover:bg-indigo-500 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Add
            </button>
          </div>
        </div>

        {webhooks.length === 0 && (
          <div className="text-center py-6">
            <p className="text-gray-500 text-sm">
              No webhooks configured. Add a URL above to receive event
              notifications.
            </p>
          </div>
        )}

        {webhooks.length > 0 && (
          <div className="space-y-2">
            {webhooks.map((webhook) => (
              <div
                key={webhook.id}
                className="flex items-center justify-between bg-gray-950 border border-gray-800 rounded p-3"
              >
                <div className="space-y-1">
                  <p className="text-sm font-mono text-gray-300">
                    {webhook.url}
                  </p>
                  <div className="flex gap-1">
                    {webhook.events.map((event) => (
                      <span
                        key={event}
                        className="inline-block px-1.5 py-0.5 text-xs rounded bg-gray-800 text-gray-400 border border-gray-700"
                      >
                        {event}
                      </span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => handleRemoveWebhook(webhook.id)}
                  className="p-1.5 text-gray-500 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <h2 className="text-sm font-medium text-gray-400 mb-3">
          API Configuration
        </h2>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">API Base URL</span>
            <span className="font-mono text-gray-300 text-xs">
              {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Auth Method</span>
            <span className="text-gray-300 text-xs">X-API-Key Header</span>
          </div>
        </div>
      </div>
    </div>
  );
}
