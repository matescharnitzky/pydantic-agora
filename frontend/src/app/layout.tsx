import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agora",
  description: "An independent playground for the Pydantic ecosystem.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
