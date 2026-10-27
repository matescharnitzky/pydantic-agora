"use client";

import { useEffect, useId, useRef } from "react";

export function Mermaid({ chart }: { chart: string }) {
  const id = useId().replaceAll(":", "");
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function render() {
      const { default: mermaid } = await import("mermaid");
      mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral" });
      const { svg } = await mermaid.render(`diagram-${id}`, chart);
      if (!cancelled && container.current) container.current.innerHTML = svg;
    }
    void render().catch(() => {
      if (!cancelled && container.current) container.current.textContent = chart;
    });
    return () => { cancelled = true; };
  }, [chart, id]);

  return <div ref={container} className="my-6 overflow-x-auto" aria-label="Architecture diagram" />;
}
