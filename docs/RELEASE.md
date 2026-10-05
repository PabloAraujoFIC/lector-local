# Release 0.2.1

Requisitos de construcción: Node.js 22, Python 3.12, uv y Rust estable. `uv sync --extra dev --frozen --python 3.12`, `npm ci`; en Linux instalar bibliotecas de desarrollo GTK/WebKit/PortAudio indicadas en CI.

`./scripts/release.sh` ejecuta validaciones, construye extensiones, prepara OCR/licencias, empaqueta el runtime Python completo en directorio y compila el instalador nativo. Windows: `scripts/release-windows.ps1`; macOS: `scripts/release-macos.sh`. Extensiones únicamente: `./scripts/release.sh --extensions-only`.

La versión se toma de package.json y se verifica con scripts/version.py. Cambiarla con `python scripts/version.py --set X.Y.Z`, actualizar `npm install --package-lock-only` y `uv lock`, y revisar documentación. Los IDs/canales están en core/reader_core/distribution.json. La clave development es pública; no es un certificado de firma.

Salidas: release/extensions, release/desktop/windows, release/desktop/macos, release/desktop/linux y release/checksums/SHA256SUMS.txt. Los archivos de cada release sustituyen los generados por ese mismo empaquetador. SHA-256: `cd release && sha256sum -c checksums/SHA256SUMS.txt`.

No se descargan pesos TTS durante el build. Se incluyen Python, motores, bibliotecas y OCR; los modelos se descargan desde Ajustes con consentimiento, HTTPS y checksum. Se usa PyInstaller onedir para evitar extracción completa en cada petición. CPU funciona sin CUDA externa.

En Arch, Windows se construye con `python scripts/build_windows_wine.py` tras preparar el entorno de docs/windows-from-linux.md. Eso no equivale a validación Windows nativa. macOS requiere runner nativo; el workflow installers.yml produce DMG de Intel y ARM64.

Sin certificados, los artefactos son SIGNING_REQUIRED; macOS puede tener firma ad-hoc, que no equivale a Developer ID/notarización. La firma pública de Windows requiere certificado y timestamp; macOS requiere Developer ID, notarización y staple. Firefox requiere firma AMO; Chrome es firmado por la tienda. CI no publica en ninguna tienda.

Antes de publicar: comprobar runtime instalado, host por navegador, audio/párrafos/seek, instalación y desinstalación nativas, enlaces públicos y licencias de dependencias copyleft. Los reports indican por separado las comprobaciones automatizadas y lo pendiente de testers.
