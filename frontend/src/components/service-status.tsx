import { cn } from "@/lib/utils";

export function ServiceStatus({ ready }: { ready: boolean }) {
  return (
    <p role="status" className="flex items-center gap-3 text-sm">
      <span aria-hidden="true" className={cn("size-2 rounded-full", ready ? "bg-emerald-600" : "bg-amber-600")} />
      {ready ? "API and database are ready" : "API is unavailable"}
    </p>
  );
}
