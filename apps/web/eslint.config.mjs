import { FlatCompat } from "@eslint/eslintrc";
import { fileURLToPath } from "node:url";
import path from "node:path";

const currentFile = fileURLToPath(import.meta.url);
const baseDirectory = path.dirname(currentFile);
const compat = new FlatCompat({ baseDirectory });
const config = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "coverage/**",
      "playwright-report/**", "next-env.d.ts",
    ],
  },
];

export default config;
