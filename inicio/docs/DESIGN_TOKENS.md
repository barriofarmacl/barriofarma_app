# Design tokens — SPA `inicio`

Referencia Capa 3 del [ADR](../../../../.cursor/docs/development/adr_inicio_frontend_architecture.md).

## Paleta (HSL en `src/index.css`)

| Token CSS | Uso |
|-----------|-----|
| `--primary` | CTAs, titulos de seccion, acentos app |
| `--secondary` | Acento salud / links secundarios |
| `--brand` | Header/footer landing, hero |
| `--background` | Fondo pagina (crema calido) |
| `--muted` | Secciones alternas, superficies suaves |
| `--card` | Tarjetas elevadas |
| `--border` | Bordes |

## Tipografia

| Rol | Familia |
|-----|---------|
| Display / headings | Fraunces |
| Body / UI | Source Sans 3 |

## Clases utilitarias (`index.css`)

- `bf-section-muted` — seccion con fondo muted
- `bf-surface-card` — tarjeta con borde y sombra
- `bf-heading-section` — titulo de seccion landing
- `bf-text-muted` — texto secundario

## Reglas

- Preferir tokens semanticos (`bg-primary`, `text-muted-foreground`) sobre `purple-*` / `gray-*` hardcodeados.
- Botones: variant `default` usa `--primary`; no override `bg-purple-700` salvo excepcion documentada.
