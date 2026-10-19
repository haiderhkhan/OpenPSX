"use client"; // Error boundaries must be Client Components (Next 16 error.js)

import { ErrorState } from "@/components/states";

// Last-resort fallback for any route that throws while rendering. Pages already catch their API errors and show
// ErrorState themselves; this only stops an unexpected crash from showing a blank page.
export default function RouteError({ error, retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      <ErrorState
        title="This page could not be shown"
        message={`Something went wrong while rendering it${error.digest ? ` (ref ${error.digest})` : ""}. Please try again.`}
        onRetry={retry}
      />
    </div>
  );
}
