# Instrucciones para agentes (workspace)

Este repo (`market-hub`) no tiene código propio: junta como submódulos de git los repos del portal de
herramientas de IA para inversión, para trabajar sobre ellos desde una sola sesión. Cada uno
sigue siendo un repo independiente, con su historial, su despliegue y su `CLAUDE.md`.

| Carpeta | Qué es | Estado |
|---|---|---|
| `market-hub-landing/` | **El portal Market Hub** (https://themarkethub.app). Landing con vídeo, la pestaña Today (el mercado del día en una frase y en una misma regla), mercados y fichas de valor con datos de Yahoo Finance y gráficos de TradingView; área privada "My Hub" con login de Google o con cuenta propia (email y contraseña), cartera y dashboard. El login se comparte con las herramientas de los subdominios. FastAPI (`src/markethub/`) + Astro (`site/`), Firestore | Desplegado (Cloud Run `market-hub`) |
| `fundamentals-lab/` | **Fundamentals Lab** (https://fundamentals.themarkethub.app, requiere login de Market Hub). Fundamentales, valoración, múltiplos a futuro, técnico, comparador y lectura con IA de cualquier empresa de EE. UU. FastAPI (`src/fundamentals/`) + Astro | Desplegado (Cloud Run `fundamentals-lab`) |
| `market-hub-playground/` | **PlayGround** (https://playground.themarkethub.app, requiere login de Market Hub). Un tablero de gráficos y tablas de mercado que el usuario compone pidiéndolo por chat: Claude elige vistas y tickers de un catálogo cerrado y el código pone todas las cifras (Yahoo Finance). No guarda nada y no lee la cartera ni la watchlist del portal. Sin tope de gasto propio, por decisión del usuario. FastAPI (`src/playground/`) + Astro | Desplegado (Cloud Run `market-hub-playground`) |
| `market-hub-peers-map/` | **Peer Map** (https://peers.themarkethub.app, requiere login de Market Hub). Un mapa de las ~1.500 mayores empresas de EE. UU. según lo que dicen que hacen: cada una junto a las que describen su negocio de forma más parecida en su informe anual (sección Business del 10-K, SEC EDGAR), con el color de cada punto según lo que se ha movido su precio (día, semana, mes, YTD, un año; Yahoo Finance). El mapa se construye a mano en local con un modelo abierto de embeddings (`make peers`) y viaja en el repo; no usa ninguna API de pago. FastAPI (`src/peermap/`) + Astro | Desplegado (Cloud Run `peer-map`) |
| `decision-signal-lab/` | **Earnings Radar**. Lee el texto de los comunicados de resultados. Dos despliegues del mismo código: https://earningsradar.app/ (público, `make deploy`) y https://radar.themarkethub.app (con login de Market Hub, `make deploy-hub`). El estudio de predicción está cerrado como resultado nulo. FastAPI (`src/decisionsignal/`) + Astro | Desplegado (Cloud Run `earnings-radar` y `earnings-radar-hub`) |

Además está `market-hub-opinion/`: los artículos de opinión del portal (un Markdown por artículo),
su validador y la skill `update-opinion` que los escribe y los publica en el Firestore del portal.
No tiene servicio ni web propios: el portal los lee y guarda los comentarios. Es un submódulo
más, y sus reglas (opinar sí, aconsejar no; los hechos son de las fuentes) están en su `CLAUDE.md`.

Y `the-market-hub-media/`: el canal de YouTube de Market Hub. Cada vídeo es una carpeta (brief,
guion, un dibujo por escena, miniatura) y se hace con tres skills, `analyze-idea`, `make-video` y
`publish-video`, a partir de los temas que da el usuario. Tampoco tiene servicio ni web: el
trabajo de pensar se hace en la sesión de Claude Code y el código solo comprueba, monta y sube a
YouTube. Sus reglas (explicar sí, aconsejar no; publicar es decisión del usuario, vídeo a vídeo)
están en su `CLAUDE.md`.

Y `market-hub-mobile/`: la app de móvil de Market Hub para iPhone y Android (Expo, React Native),
que lleva My Hub al teléfono. Tampoco tiene servicio propio: habla con la API del portal
(`market-hub-landing`), con un token en vez de la cookie de sesión (`tokens.py` del portal). Un
cambio en lo que responde esa API, o en los colores y formatos de la web del portal, se hace
también en la app. Se compila con EAS a mano, y publicar en una tienda es decisión del usuario,
versión a versión. Sus reglas están en su `CLAUDE.md`.

Los tres servicios comparten stack y estilo visual (Python 3.12 con `uv`, web Astro con el tema oscuro de
Market Hub, un contenedor en Cloud Run, todo lanzado a mano desde el `Makefile`), bajo la marca
Market Hub y el dominio `themarkethub.app` (DNS en Cloudflare, mapeos de dominio de Cloud Run).

Desde el 2026-10-05 las dos herramientas son secciones del portal: los tres sitios comparten el
mismo `site/src/styles/global.css` (se copia del de `market-hub-landing`; cada herramienta añade
lo suyo al final) y las mismas pestañas de empresa (`Price · Fundamentals · Results release`).
Desde el 2026-10-06 la cabecera pública del portal es `Today · Markets · News · Opinion · Media` y las herramientas
solo se enlazan desde My Hub, el área privada. Las dos herramientas, que piden login, son
secciones de My Hub: llevan su misma navegación lateral (`HubNav.astro` en cada una, copia de la
de `App.astro` en `market-hub-landing`) y encima su barra propia. Un cambio de estilo base, o de la
navegación de My Hub, se hace en los tres, y también en `market-hub-playground` y en
`market-hub-peers-map` (desde el 2026-10-08), que llevan su copia de `global.css` y de `HubNav.astro`. En `earningsradar.app` el radar conserva su cabecera
propia.

Las noticias del portal se actualizan sin nada programado: una visita que las encuentra viejas
pide el refresco (`market-hub-landing/docs/HANDOFF.md`).

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
