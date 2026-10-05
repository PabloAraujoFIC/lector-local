# Entregas para pruebas nativas

La guía para entregar archivos y probar cada sistema/navegador está en
`installers/GUIA-TESTERS.md`, con copia en `artifacts/releases/GUIA-TESTERS.md`.
`scripts/package_testers.py` prepara el instalador Linux por usuario `.run` y
el XPI Firefox para carga temporal, a partir de los paquetes ya verificados.
Las entregas y sus SHA-256 se enumeran en `artifacts/releases/testers.json`.

El repositorio contiene una única aplicación con configuración por plataforma. Windows x64 se compila desde Arch con Wine y cargo-xwin; la validación en Windows real sigue pendiente. macOS requiere compilación nativa. No se presentan builds sin firma como firmados.

| Plataforma | Entrega prevista | Estado actual |
|---|---|---|
| Linux x64 | DEB + TAR portátil | Generado en este equipo Arch; requiere GTK3, WebKitGTK 4.1, PortAudio y glibc compatible |
| Windows x64 | NSIS `*-setup.exe` por usuario | Compilado con Wine/cargo-xwin; voces/OCR y Native Messaging probados bajo Wine; validación Windows real pendiente |
| macOS Intel | `.app` dentro de `.dmg` | Receta integrada; compilación nativa pendiente |
| macOS Apple Silicon | `.app` dentro de `.dmg` | Receta integrada; compilación nativa pendiente |
| Chromium / Gecko | ZIP de extensión | Generados sin firma; integración real probada en Zen Linux |

## Obtener Windows y macOS sin tener esos equipos

En este equipo, Windows también puede construirse con `.venv/bin/python scripts/build_windows_wine.py`. Entregas separadas en `artifacts/releases/windows/`. Véase `docs/windows-from-linux.md` para el entorno preparado y `installers/windows/LEEME.txt` para testers. El motor se instala junto con sus recursos y bibliotecas de Visual C++, sin extraer los modelos en cada petición.

Sube el código a un repositorio GitHub y ejecuta **Actions → Native installers for manual testing → Run workflow**. El workflow `.github/workflows/installers.yml` compila en Windows, macOS Intel, macOS ARM64 y Ubuntu, ejecuta los checks y adjunta cuatro artefactos descargables. No publica releases ni usa credenciales. Aún no se ha ejecutado: este directorio no tiene repositorio remoto autenticado.

Los runners nativos generan instaladores, pero no certifican audio de altavoces, menús del navegador, Gatekeeper o instalación/desinstalación en un equipo de usuario. Usa `docs/manual-validation.md` para tus pruebas.

## Compilar en cada sistema

Instala Python 3.12 mediante uv, Node 22, Rust estable y los requisitos Tauri del SO: Windows necesita Visual Studio Build Tools con C++ y WebView2; macOS Xcode Command Line Tools; Linux las bibliotecas anteriores y herramientas de empaquetado. Desde la raíz:

```sh
uv sync --extra dev --python 3.12 --frozen
npm ci
uv run --extra dev python scripts/verify.py
uv run --extra dev python scripts/build_release.py
```

El script elige la configuración `tauri.windows.conf.json` o `tauri.macos.conf.json` automáticamente mediante Tauri. Entregas en `artifacts/releases/`, con tamaños y SHA-256 en `release.json`. Los paquetes incluyen Python, Kokoro y sus voces, Piper con voz española y datos OCR para seis idiomas. El proceso de build descarga y verifica estos recursos, y ejecuta `lector-core self-test` con almacenamiento vacío y red bloqueada antes de producir instaladores. Windows incluye el instalador offline de WebView2. macOS se construye una vez en Intel y otra en ARM64; no se etiqueta un binario como universal. Consulta `docs/bundled-resources.md` para versiones y avisos.

## Registro del navegador y retirada

Windows NSIS instala por usuario, registra Firefox/Zen en HKCU y llama al core para retirar sus registros antes de desinstalar. Chromium requiere copiar su ID desde la página de extensiones a **Ajustes → Navegadores**, ya que la extensión de desarrollo no tiene ID publicado estable. No se registra una lista abierta de orígenes.

macOS: arrastra la app desde el DMG a Aplicaciones **antes** de registrar el navegador desde Ajustes. No hay postinstall en un DMG. Antes de eliminar la app puedes retirar los registros con:

```sh
"/Applications/Lector Local.app/Contents/MacOS/lector-core" install-host --uninstall
```

Linux portátil: extrae el TAR en una ruta permanente, abre `lector-local-desktop` y registra desde Ajustes. Antes de mover/eliminar esa carpeta ejecuta `./lector-core install-host --uninstall`. La retirada solo borra manifests cuyo nombre y ejecutable coincidan con esa instalación; conserva registros reemplazados por otra instalación, documentos, modelos y preferencias. Linux/macOS usan el directorio de hosts de Firefox, compatible con Zen en Linux según la prueba real.

Las extensiones ZIP para Gecko se cargan temporalmente desde `about:debugging`; se pierden al reiniciar. La instalación permanente requiere firma Mozilla. Chromium se carga descomprimiendo el ZIP y usando «Cargar descomprimida».

## Firma de distribución

`uv run --extra dev python scripts/build_release.py --signed` exige credenciales previamente aprovisionadas y aborta si faltan. No las incluyas en el código ni en el ZIP.

- Windows: certificado de firma instalado para el usuario, `signtool.exe` accesible (o `LECTOR_SIGNTOOL`), `LECTOR_WINDOWS_CERTIFICATE_THUMBPRINT` y `LECTOR_WINDOWS_TIMESTAMP_URL` del proveedor. Firma y verifica el core antes de incluirlo; Tauri llama al mismo firmador para el ejecutable y el instalador. Cada firma se verifica con `signtool verify /pa /all`.
- macOS: certificado Developer ID en el llavero y variables `APPLE_SIGNING_IDENTITY`, `APPLE_ID`, `APPLE_PASSWORD` (contraseña específica de aplicación), `APPLE_TEAM_ID`. PyInstaller firma las bibliotecas del core y Tauri firma/notariza la app. La entrega exige `codesign --verify`, ticket stapled válido y evaluación `spctl` positiva. El entitlement de library validation permite las bibliotecas Python empaquetadas y debe revisarse en la prueba nativa.
- Gecko: todavía no se ha enviado a Mozilla ni se ha obtenido XPI firmado. El flujo de firma nativa no firma extensiones.

Sin certificados no se han ejecutado estos flujos de firma. Las entregas predeterminadas son builds de prueba sin firma de editor; macOS puede incorporar firma ad-hoc y todavía quedar bloqueado por Gatekeeper.

Referencias: [requisitos Tauri](https://v2.tauri.app/start/prerequisites/), [NSIS y hooks](https://v2.tauri.app/distribute/windows-installer/), [Authenticode](https://v2.tauri.app/distribute/sign/windows/), [Developer ID y notarización](https://v2.tauri.app/distribute/sign/macos/), [runners GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
