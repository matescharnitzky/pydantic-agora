import Link from "next/link";
import { ServiceStatus } from "@/app/_components/service-status";

export const dynamic = "force-dynamic";

export default async function Home() {
  let ready = false;
  try {
    const response = await fetch(`${process.env.API_BASE_URL ?? "http://127.0.0.1:8000"}/ready`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    ready = response.ok;
  } catch {
    // Keep the shell accessible while the API is starting or unavailable.
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-8 px-8 py-16">
      <header className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">Local development</p>
        <h1 className="text-6xl font-semibold tracking-tight">Agora</h1>
        <p className="max-w-xl text-xl leading-relaxed text-stone-600">
          Explore, compose, and evaluate the Pydantic ecosystem.
        </p>
      </header>
      <section aria-label="Service readiness" className="rounded-xl border border-stone-200 bg-white p-6">
        <ServiceStatus ready={ready} />
      </section>
      <Link href="/docs" className="font-medium underline underline-offset-4">Documentation</Link>
      <footer className="text-sm leading-relaxed text-stone-500">
        Independent open-source project. Not affiliated with or endorsed by Pydantic.
      </footer>
    </main>
  );
}
