"use client";

import { FlaskConical } from "lucide-react";

export default function CalibrationPage() {
  return (
    <div className="flex flex-col items-center justify-center h-96 space-y-4">
      <FlaskConical className="w-16 h-16 text-gray-600" />
      <h1 className="text-2xl font-bold text-white">Calibration Lab</h1>
      <p className="text-gray-400">Coming Soon</p>
      <p className="text-sm text-gray-600 max-w-md text-center">
        The Calibration Lab will allow you to test policy changes against
        historical decisions, compare judgment outcomes, and fine-tune
        decision thresholds before deploying to production.
      </p>
    </div>
  );
}
