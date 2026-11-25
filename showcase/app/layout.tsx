import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Recognitio, the verified review packet",
  description:
    "Recognitio pulls the changes from a pull request or a commit range, with the context a reviewer needs, into one verified review packet.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
