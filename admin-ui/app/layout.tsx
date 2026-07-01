import type { Metadata } from "next";
import "./globals.css";
import ThemeRegistry from "./theme-registry";

export const metadata: Metadata = {
  title: "Hang Cú VIP Admin",
  description: "Admin dashboard for Hang Cú VIP",
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
