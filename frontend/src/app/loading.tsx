import { Loading } from "@/components/states";

// Shown while a server page fetches from the API (every route renders per request).
export default function RouteLoading() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <div className="h-8 w-48 animate-pulse rounded bg-muted" />
      <Loading rows={6} />
    </div>
  );
}
