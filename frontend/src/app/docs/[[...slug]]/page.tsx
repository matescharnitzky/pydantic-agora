import { notFound } from "next/navigation";
import { DocsBody, DocsPage, DocsTitle, DocsDescription } from "fumadocs-ui/page";
import defaultMdxComponents, { createRelativeLink } from "fumadocs-ui/mdx";
import { Mermaid } from "../_components/mermaid";
import { source } from "@/lib/docs";

type Props = { params: Promise<{ slug?: string[] }> };

export default async function Page({ params }: Props) {
  const { slug } = await params;
  const page = source.getPage(slug);
  if (!page) notFound();
  const Content = page.data.body;
  return (
    <DocsPage toc={page.data.toc}>
      <DocsTitle>{page.data.title}</DocsTitle>
      <DocsDescription>{page.data.description}</DocsDescription>
      <DocsBody>
        <Content components={{ ...defaultMdxComponents, Mermaid, a: createRelativeLink(source, page) }} />
      </DocsBody>
    </DocsPage>
  );
}

export function generateStaticParams() {
  return source.generateParams();
}

export async function generateMetadata({ params }: Props) {
  const page = source.getPage((await params).slug);
  if (!page) notFound();
  return { title: `${page.data.title} | Agora`, description: page.data.description };
}
