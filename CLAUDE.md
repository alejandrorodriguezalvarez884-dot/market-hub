# Instrucciones para agentes (workspace)

Este repo (`market-hub`) no tiene código propio: junta como submódulos de git los tres repos del portal de
herramientas de IA para inversión, para trabajar sobre ellos desde una sola sesión. Cada uno
sigue siendo un repo independiente, con su historial, su despliegue y su `CLAUDE.md`.

| Carpeta | Qué es | Estado |
|---|---|---|
| `market-hub-landing/` | **El portal Market Hub** (https://themarkethub.app). Landing con vídeo, la pestaña Today (el mercado del día en una frase y en una misma regla), mercados y fichas de valor con datos reales de FMP; área privada "My Hub" con login de Google, cartera y dashboard. El login se comparte con las herramientas de los subdominios. FastAPI (`src/markethub/`) + Astro (`site/`), Firestore | Desplegado (Cloud Run `market-hub`) |
| `fundamentals-lab/` | **Fundamentals Lab** (https://fundamentals.themarkethub.app, requiere login de Market Hub). Fundamentales, valoración, múltiplos a futuro, técnico, comparador y lectura con IA de cualquier empresa de EE. UU. FastAPI (`src/fundamentals/`) + Astro | Desplegado (Cloud Run `fundamentals-lab`) |
| `decision-signal-lab/` | **Earnings Radar**. Lee el texto de los comunicados de resultados. Dos despliegues del mismo código: https://earningsradar.app/ (público, `make deploy`) y https://radar.themarkethub.app (con login de Market Hub, `make deploy-hub`). El estudio de predicción está cerrado como resultado nulo. FastAPI (`src/decisionsignal/`) + Astro | Desplegado (Cloud Run `earnings-radar` y `earnings-radar-hub`) |

Los tres comparten stack y estilo visual (Python 3.12 con `uv`, web Astro con el tema oscuro de
Market Hub, un contenedor en Cloud Run, todo lanzado a mano desde el `Makefile`), bajo la marca
Market Hub y el dominio `themarkethub.app` (DNS en Cloudflare, mapeos de dominio de Cloud Run).

Desde el 2026-10-05 las dos herramientas son secciones del portal: los tres sitios llevan la misma
cabecera (`Today · Markets · Fundamentals · Earnings`), el mismo `site/src/styles/global.css` (se
copia del de `market-hub-landing`; cada herramienta añade lo suyo al final) y las mismas pestañas
de empresa (`Price · Fundamentals · Results release`). Un cambio de cabecera o de estilo base se
hace en los tres. En `earningsradar.app` el radar conserva su cabecera propia.

## Cómo trabajar aquí

- **Antes de tocar un repo, lee su `CLAUDE.md` y su `docs/HANDOFF.md`.** Sus reglas mandan
  dentro de su carpeta. Las de abajo son las comunes, no las sustituyen.
- **Cada cambio se hace, se commitea y se sube dentro del submódulo**, en su propio repo
  (`git -C fundamentals-lab …` o con `cd`), nunca en la raíz de este repo. Comandos como `make test` se lanzan desde la
  carpeta de cada repo.
- Si la tarea cruza repos (por ejemplo, un enlace del portal a una herramienta), se hace un
  commit en cada repo afectado y se dice en cuáles.
- **Este repo solo guarda punteros a commits.** `scripts/sync.sh` (que se lanza solo al abrir una
  sesión) deja cada submódulo en la punta de `main`. Mover los punteros aquí es opcional: si se
  hace, es un commit aparte ("Bump submodules") y nunca sustituye al push en el repo hijo.
- Nada de código de producto en la raíz de este repo. Hasta el 2026-10-05 este repo era el portal;
  ese código y su historial están ahora en `market-hub-landing`.

## Reglas comunes que no se negocian

- **Nada de trading.** No se escribe código que envíe órdenes ni que se conecte a un broker, y no
  se usa ningún conector de broker (IBKR u otro), ni siquiera para descargar precios o importar
  posiciones.
- **Describir, no recomendar.** Ninguna web dice comprar, vender o mantener, ni da predicciones,
  precios objetivo o alertas de oportunidad.
- **Los servicios públicos gastan con las claves del usuario.** No se suben ni se quitan topes de
  gasto ni límites por IP sin preguntarle, y antes de gastar en una API se le pide permiso.
- **Claves solo en `.env` o en el entorno.** Nunca en ningún repo, en logs ni en commits.
- **Nada programado y nada en GitHub Actions.** Todo se lanza a mano desde el `Makefile` de cada repo.
- **Los resultados nulos se reportan tal cual.**

## Convenciones

- Hablar con el usuario en español. Código y comentarios en inglés.
- Al terminar una tarea relevante, actualizar "Dónde estamos" en el `docs/HANDOFF.md` del repo que
  se tocó.
