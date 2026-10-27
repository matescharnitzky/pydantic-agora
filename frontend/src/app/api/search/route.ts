import { createFromSource } from "fumadocs-core/search/server";
import { source } from "@/lib/docs";

export const { GET } = createFromSource(source);
