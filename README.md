# Lector Local

Aplicación de escritorio y extensión para leer documentos, selecciones y artículos con voz local. React/TypeScript + Tauri + Python; Kokoro y Piper CPU, OCR y Native Messaging. La voz se descarga una vez desde Ajustes con consentimiento y SHA-256. Después, texto y audio se procesan sin Internet.

- [Instalación y pruebas por sistema/navegador](docs/TESTERS.md)
- [Construcción y release](docs/RELEASE.md)
- [Chrome Web Store](docs/CHROME_STORE.md)
- [AMO / Firefox / Zen](docs/FIREFOX_AMO.md)
- [Fuentes Firefox para revisión](docs/FIREFOX_BUILD.md)
- [Privacidad](docs/PRIVACY.md)
- [Avisos de terceros](THIRD_PARTY_NOTICES.md)

Desarrollo: `uv sync --extra dev --frozen --python 3.12`, `npm ci`, `npm run dev`. Extensión: `LECTOR_CHANNEL=development npm run build --workspace @lector/extension`. Los IDs están centralizados en core/reader_core/distribution.json. Validar con `.venv/bin/python scripts/verify.py`; generar entregas con `./scripts/release.sh`.

No se publican tiendas ni se firman entregas sin credenciales. Los paquetes unsigned están identificados como SIGNING_REQUIRED. La validación nativa manual queda registrada por plataforma, separada de las pruebas automatizadas.

## Descargar para pruebas

Abrir la [Release 0.2.0](https://github.com/PabloAraujoFIC/lector-local/releases/tag/v0.2.0) y escoger el archivo de su sistema. No descargar «Source code» si sólo se quiere instalar.

| Sistema o navegador | Archivo |
|---|---|
| Windows 10/11 · x64 | `lector-local-0.2.0-windows-x64-setup.exe` |
| Linux Debian/Ubuntu · x64 | `lector-local-0.2.0-linux-x64.deb` |
| Linux Arch/otras · x64 | `lector-local-0.2.0-linux-x64.tar.gz` (si figura en la Release) |
| macOS · Apple Silicon | `lector-local-0.2.0-macos-arm64.dmg` (sólo si la build nativa termina correctamente) |
| macOS · Intel | `lector-local-0.2.0-macos-x64.dmg` (sólo si la build nativa termina correctamente) |
| Chrome / Chromium / Edge / Brave | `lector-local-0.2.0-chrome.zip` |
| Firefox / Zen · Gecko 140+ | `lector-local-0.2.0-firefox.zip` (instalación temporal; firma AMO pendiente) |

Primero instalar el escritorio y descargar una voz desde Ajustes. Después añadir la extensión siguiendo [la guía paso a paso](docs/TESTERS.md). Comprobar SHA256SUMS.txt incluido en la Release. Es una entrega de pruebas sin certificados de producción: **SIGNING_REQUIRED**. La Release sólo ofrece archivos que se han generado realmente; las plataformas pendientes se indican en sus notas.

