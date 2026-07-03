import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "SpeechEval — TTS Evaluation Infrastructure",
  description:
    "Reproducible TTS evaluation, benchmarking, and regression testing.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
