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

Abrir la [Release 0.2.1](https://github.com/PabloAraujoFIC/lector-local/releases/tag/v0.2.1) y escoger el archivo de su sistema. No descargar «Source code» si sólo se quiere instalar.

| Sistema o navegador | Descargar |
|---|---|
| Windows 10/11 · x64 | [Instalador .exe](https://github.com/PabloAraujoFIC/lector-local/releases/download/v0.2.1/lector-local-0.2.1-windows-x64-setup.exe) |
| Ubuntu 22.04+ / Debian 12+ · x64 | [Paquete .deb](https://github.com/PabloAraujoFIC/lector-local/releases/download/v0.2.1/lector-local-0.2.1-linux-x64.deb) |
| Arch / otras distribuciones · x64 | [Paquete .tar.gz](https://github.com/PabloAraujoFIC/lector-local/releases/download/v0.2.1/lector-local-0.2.1-linux-x64.tar.gz) |
| macOS 14+ · Apple Silicon | [Instalador .dmg](https://github.com/PabloAraujoFIC/lector-local/releases/download/v0.2.1/lector-local-0.2.1-macos-arm64.dmg) |
| macOS 14+ · Intel | [Instalador .dmg](https://github.com/PabloAraujoFIC/lector-local/releases/download/v0.2.1/lector-local-0.2.1-macos-x64.dmg) |
| Chrome / Chromium / Edge / Brave | [Extensión .zip](https://github.com/PabloAraujoFIC/lector-local/releases/download/v0.2.1/lector-local-0.2.1-chrome.zip) |
| Firefox / Zen · Gecko 140+ | [Extensión .zip (temporal)](https://github.com/PabloAraujoFIC/lector-local/releases/download/v0.2.1/lector-local-0.2.1-firefox.zip) |

Primero instalar el escritorio y descargar una voz desde Ajustes. Después añadir la extensión siguiendo [la guía paso a paso](docs/TESTERS.md). Comprobar [SHA256SUMS-downloads.txt](https://github.com/PabloAraujoFIC/lector-local/releases/download/v0.2.1/SHA256SUMS-downloads.txt) incluido en la Release. Es una entrega de pruebas sin certificados de producción: **SIGNING_REQUIRED**. Los instaladores se han construido en runners nativos de GitHub Actions. La validación manual de instalación, interfaz y audio en Windows/macOS queda a cargo de los testers. Si el repositorio es privado, las descargas requieren acceso concedido por el propietario.

