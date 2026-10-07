# Market Hub (workspace)

Los repos del portal de herramientas de IA para inversión, juntos como submódulos de git para
trabajar sobre ellos desde un solo sitio, sin fusionarlos:

- [`market-hub-landing`](https://github.com/alejandrorodriguezalvarez884-dot/market-hub-landing): el portal Market Hub (login, cartera, dashboard).
- [`fundamentals-lab`](https://github.com/alejandrorodriguezalvarez884-dot/fundamentals-lab): fundamentales, valoración y técnico.
- [`decision-signal-lab`](https://github.com/alejandrorodriguezalvarez884-dot/decision-signal-lab): Earnings Radar.
- [`market-hub-opinion`](https://github.com/alejandrorodriguezalvarez884-dot/market-hub-opinion): los artículos de opinión del portal y la skill que los escribe.
- [`the-market-hub-media`](https://github.com/alejandrorodriguezalvarez884-dot/the-market-hub-media): el canal de YouTube.
- [`market-hub-mobile`](https://github.com/alejandrorodriguezalvarez884-dot/market-hub-mobile): la app de móvil (iPhone y Android), que habla con la API del portal.

El contexto común para agentes está en [`CLAUDE.md`](CLAUDE.md). Hasta el 2026-10-05 este repo
era el código del portal; ese código, con su historial, está ahora en `market-hub-landing`.

## Abrirlo

**Claude Code en la web:** se crea la sesión sobre `market-hub` y se seleccionan también los
cuatro repos (si no, se pueden leer pero no hacer push en ellos). Al arrancar, un hook ejecuta
`scripts/sync.sh` y deja los cuatro en la punta de `main`.

**GitHub Codespaces:** *Code → Codespaces → Create*. El devcontainer pide permiso de escritura
sobre los cuatro repos, instala `uv` y Node y ejecuta `scripts/sync.sh`.

**En local:**

```bash
git clone --recurse-submodules https://github.com/alejandrorodriguezalvarez884-dot/market-hub.git
cd market-hub && scripts/sync.sh
```

## Día a día

```bash
scripts/sync.sh                        # traer lo último de main en los cuatro repos
cd fundamentals-lab                    # trabajar dentro de un repo...
git commit -am "…" && git push         # ...y subir el cambio a ese repo

# Opcional: fijar en el workspace los commits actuales de cada repo
git add market-hub-landing fundamentals-lab decision-signal-lab market-hub-opinion && git commit -m "Bump submodules" && git push
```

Para añadir otro repo: `git submodule add -b main <url> <carpeta>` y una fila en `CLAUDE.md`.
