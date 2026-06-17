import type { Metadata } from "next";
import "./globals.css";
import ThemeRegistry from "./theme-registry";

export const metadata: Metadata = {
  title: "Prive Admin",
  description: "Admin dashboard for Prive Bot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body>
        <ThemeRegistry>{children}</ThemeRegistry>
      </body>
    </html>
  );
}
