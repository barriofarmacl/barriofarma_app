# Barriofarma — SPA `inicio`

## Stack oficial de este frontend (decisión de proyecto Barriofarma)

**Esta combinación es el stack oficial del proyecto Barriofarma** para la SPA bajo la ruta `inicio` dentro de **barriofarma_app**:

| Capa | Herramienta |
|------|-------------|
| UI | **React 18** + componentes estilo **shadcn/ui** (primitivas **Radix UI**, **Tailwind CSS**, **class-variance-authority**) en `src/components/ui/` |
| Build | **Vite** + **TypeScript** |
| Integración Frappe | **`frappe-react-sdk`** (sesión por cookie, `useFrappeAuth`, `useFrappeGetCall`, etc.) |

No se usa **Frappe UI (Vue 3)** en esta SPA. Las guías y skills que lo prescriben (p. ej. `frappe-frontend-development`) aplican solo como **referencia de buenas prácticas** (proxy, auth, loading, build), no como mandato de migración: **no hay plan de pasar esta SPA a Vue**.

Alcance actual acordado: **landing informativa**, **login** hacia el Desk (`/app`) o catalogo terreno (`/inicio/catalogo` segun rol), y **catalogo + carrito** para vendedores en terreno. Nuevas pantallas deben seguir el mismo patron: **SDK + cookies**; evitar `fetch` ad hoc que ignore la sesion.

**Arquitectura frontend (ADR):** ver [adr_inicio_frontend_architecture.md](../../../../.cursor/docs/development/adr_inicio_frontend_architecture.md) (submodule methodology en monorepo dev).

**Design tokens:** ver [docs/DESIGN_TOKENS.md](docs/DESIGN_TOKENS.md).

**Feature catalogo:** `src/features/catalogo/` (api, hooks, context, components).

**Fecha de ratificacion stack:** 2026-04-20 (React+shadcn+sdk). **Gate calidad brand:** 2026-07-11 (Architect).

---

# React + TypeScript + Vite (plantilla base)

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type aware lint rules:

- Configure the top-level `parserOptions` property like this:

```js
export default tseslint.config({
  languageOptions: {
    // other options...
    parserOptions: {
      project: ['./tsconfig.node.json', './tsconfig.app.json'],
      tsconfigRootDir: import.meta.dirname,
    },
  },
})
```

- Replace `tseslint.configs.recommended` to `tseslint.configs.recommendedTypeChecked` or `tseslint.configs.strictTypeChecked`
- Optionally add `...tseslint.configs.stylisticTypeChecked`
- Install [eslint-plugin-react](https://github.com/jsx-eslint/eslint-plugin-react) and update the config:

```js
// eslint.config.js
import react from 'eslint-plugin-react'

export default tseslint.config({
  // Set the react version
  settings: { react: { version: '18.3' } },
  plugins: {
    // Add the react plugin
    react,
  },
  rules: {
    // other rules...
    // Enable its recommended rules
    ...react.configs.recommended.rules,
    ...react.configs['jsx-runtime'].rules,
  },
})
```
