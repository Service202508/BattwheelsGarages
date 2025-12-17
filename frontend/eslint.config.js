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
      // React specific rules - all off for existing codebase compatibility
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "react/display-name": "off",
      "react/no-unescaped-entities": "off",
      "react/no-unknown-property": "off",
      "react/no-unstable-nested-components": "off",

      // General rules
      "no-unused-vars": "off",
      "no-console": "off",
      "prefer-const": "off",
      "no-var": "off",
      "no-undef": "off",

      // React Hooks rules - off for compatibility
      "react-hooks/rules-of-hooks": "off",
      "react-hooks/exhaustive-deps": "off",
    },
  },
  {
    ignores: ["node_modules/", "build/", "dist/", "*.config.js", "craco.config.js"],
  },
];
