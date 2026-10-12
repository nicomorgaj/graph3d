# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado [SemVer](https://semver.org/lang/es/).

## [0.1.0] - 2026-10-12

### Añadido
- Visor 3D autocontenido (un solo HTML, canvas 2D con proyección propia, sin librerías externas).
- Diseño en dos niveles con `numpy`: esferas de comunidad con colisión y nodos dentro de cada esfera.
- Áreas automáticas por carpeta de primer nivel (`--depth`, `--max-areas`) o a mano con `--areas-config`.
- Filtros por área y por comunidad con selección múltiple, búsqueda, selección de nodo con vecinos y etiquetas sin solapes.
- Rotación automática con velocidad configurable (0.1× a 8×) y opción de girar al revés.
- Interfaz en español e inglés (`--lang`).
- Vista previa estática en PNG (`--png`) sin necesidad de navegador.
- Lanzador `bin/graph3d` y comprobación en la CLI: siempre corre dentro de un venv.
- Pruebas en Python (`unittest`) y pruebas del visor en `node` con un DOM simulado.
