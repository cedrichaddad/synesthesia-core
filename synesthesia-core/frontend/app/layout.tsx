import type { Metadata } from "next";
import { Courier_Prime, Rajdhani } from 'next/font/google';
import "./globals.css";

const courierPrime = Courier_Prime({
  weight: ['400', '700'],
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});

const rajdhani = Rajdhani({
  weight: ['400', '600', '700'],
  subsets: ['latin'],
  variable: '--font-tech',
  display: 'swap',
});

export const metadata: Metadata = {
  title: "Synesthesia | Sonic Lab",
  description: "A cyberpunk music discovery interface featuring a holographic workbench, modular synth controls, and audio spectral analysis.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${courierPrime.variable} ${rajdhani.variable}`}>
      <body>{children}</body>
    </html>
  );
}
