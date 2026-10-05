import js from "@eslint/js";
import ts from "typescript-eslint";
import globals from "globals";
export default ts.config(
  { ignores: ["**/dist/**", "**/target/**"] },
  js.configs.recommended,
  { languageOptions: { globals: globals.node } },
  ...ts.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
    rules: { "@typescript-eslint/no-explicit-any": "error" },
  },
);
