# Sortarr UI

React + TypeScript + Vite frontend for Sortarr.

## Development

```bash
npm install
npm run dev
```

## Testing

### API Contract Tests

The project includes comprehensive API contract tests that validate the backend API responses match the TypeScript type definitions. These tests run against the real backend API (not mocked) to catch:

- Type mismatches (e.g., using 'name' instead of 'channel_title')
- Missing required fields
- Incorrect data structures (e.g., returning object when array expected)
- Field name inconsistencies across endpoints

**Run API contract tests:**

```bash
# Against production
API_BASE_URL=https://sortarr.bateau.cloud npm run test:api

# Against local backend
API_BASE_URL=http://localhost:8080 npm run test:api
```

**Run all E2E tests:**

```bash
npm run test:e2e          # Headless
npm run test:e2e:ui       # Interactive UI
npm run test:e2e:headed   # With browser visible
```

### Why API Contract Tests Matter

These tests would have caught the production bugs we fixed:
- `/api/subscriptions` returning wrong field names ('name' vs 'channel_title')
- `/api/subscriptions/stats` returning object instead of array
- Type mismatches between backend and frontend

**These tests must pass before deployment.**

## Build

```bash
npm run build
```

---

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
