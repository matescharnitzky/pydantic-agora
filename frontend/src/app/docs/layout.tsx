import { DocsLayout } from "fumadocs-ui/layouts/docs";
import { RootProvider } from "fumadocs-ui/provider/next";
import { source } from "@/lib/docs";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <RootProvider theme={{ enabled: false }}>
      <DocsLayout tree={source.getPageTree()} nav={{ title: "Agora", url: "/" }}
        themeSwitch={{ enabled: false }}>
        {children}
      </DocsLayout>
    </RootProvider>
  );
}
