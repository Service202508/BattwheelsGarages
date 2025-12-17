import globals from "globals";
import pluginReact from "eslint-plugin-react";
import pluginReactHooks from "eslint-plugin-react-hooks";

export default [
  {
    files: ["**/*.{js,mjs,cjs,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        process: "readonly",
      },
    },
    plugins: {
      react: pluginReact,
      "react-hooks": pluginReactHooks,
    },
    settings: {
      react: {
        version: "detect",
      },
    },
    rules: {
      // React specific rules
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "react/display-name": "off",
      "react/no-unescaped-entities": "off",
      "react/no-unknown-property": ["error", { ignore: ["jsx", "cmdk-input-wrapper", "global"] }],
      "react/no-unstable-nested-components": "off",

      // General rules
      "no-unused-vars": ["warn", { argsIgnorePattern: "^_", varsIgnorePattern: "^_|^React$" }],
      "no-console": "off",
      "prefer-const": "warn",
      "no-var": "error",
      "no-undef": "error",

      // React Hooks rules
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "off",
      "react-hooks/set-state-in-effect": "off",
    },
  },
  {
    ignores: ["node_modules/", "build/", "dist/", "*.config.js", "craco.config.js"],
  },
];
