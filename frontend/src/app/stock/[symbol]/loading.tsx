import { Loading } from "@/components/states";

export default function StockLoading() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
      <div className="h-8 w-48 animate-pulse rounded bg-muted" />
      <Loading label="Loading stock intelligence data..." rows={6} />
    </div>
  );
}

