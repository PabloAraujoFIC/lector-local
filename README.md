# Lector Local

Lector de documentos y páginas web con voz ejecutada en tu dispositivo. Monorepo con **Tauri 2 + React + TypeScript**, una extensión **WebExtensions** para Chromium/Firefox y **un único core Python** que controla extracción, síntesis, audio, caché y progreso.

Este repositorio contiene una primera versión funcional en desarrollo. No utiliza API de IA, cuentas, servicios TTS cloud, analytics ni descargas silenciosas. Los instaladores incluyen Kokoro, Piper con voz española y OCR local. No hace falta instalar Python ni descargar modelos para leer. Consulta [estado y límites](docs/status.md) antes de distribuirlo como producto terminado.

Para entregar la aplicación, consulta la [guía paso a paso para testers](installers/GUIA-TESTERS.md).
Los instaladores y modelos generados se mantienen fuera de Git. Windows puede
compilarse desde Linux con el [entorno Wine y cargo-xwin](docs/windows-from-linux.md);
el [workflow de instaladores](.github/workflows/installers.yml) también permite
compilar en runners nativos Windows, Linux y macOS. La entrega macOS sigue pendiente.

## Inicio rápido

Requisitos: Python **3.12 recomendado** (el core declara 3.11–3.14), Node **22.12+**, Rust estable y los [requisitos nativos de Tauri](https://v2.tauri.app/start/prerequisites/). ONNX Runtime y PortAudio deben funcionar en tu plataforma. Las dependencias quedan bloqueadas en `uv.lock`, `package-lock.json` y `Cargo.lock`.

```sh
uv sync --python 3.12 --extra dev
npm ci
uv run python scripts/package_core.py
npm run dev
```

En Windows utiliza PowerShell y `uv run` para evitar diferencias de activación del entorno. Linux necesita WebKitGTK 4.1, GTK 3, bibliotecas de audio y herramientas de compilación; macOS necesita Xcode Command Line Tools; Windows necesita MSVC Build Tools y WebView2.

Abre **Ajustes → Descargar Kokoro**. Antes de descargar se muestran licencia Apache-2.0, destino y tamaño: **354 MB** (338 MiB). Los dos archivos tienen SHA-256 fijado en el código. Después abre un TXT, pulsa Play y utiliza pausa, reanudar y detener. También puedes arrastrar archivos, elegir voz y velocidad, o pulsar un párrafo.

Instalación del modelo desde terminal, con confirmación interactiva:

```sh
uv run python scripts/install_model.py
```

`--accept` solo debe utilizarse cuando ya has aceptado descargar el modelo. Para importar modelos offline puedes copiar `kokoro-v1.0.onnx` y `voices-v1.0.bin` desde otro equipo al directorio `models/kokoro` que muestra Ajustes. El runtime no descarga archivos ausentes.

### Entorno preparado en este equipo

Durante el desarrollo se ha creado `.venv` con Python 3.12, instalado dependencias y descargado Kokoro en `.runtime/models/kokoro`. Para usar esos modelos sin copiarlos:

```sh
LECTOR_DATA_DIR="$PWD/.runtime" npm run dev
```

La muestra de voz española está en `artifacts/prueba-espanol.wav`. Es un artefacto local, excluido de Git.

## Documentos

Soporta TXT, PDF con texto, ODT, DOCX, EPUB en orden de spine, Markdown, HTML/HTM y RTF. La extracción se ejecuta fuera de la UI. Se normalizan espacios, Unicode, saltos artificiales y palabras partidas; el chunking preserva palabras y offsets por párrafo. El escritorio solicita páginas de 80 párrafos en lugar de renderizar todo el libro.

Los PDF utilizan PyMuPDF con orden espacial, eliminación heurística de encabezados/pies repetidos y números de página. PDFs cifrados muestran un error. Los documentos con páginas sin texto requieren activar OCR en Ajustes. El motor OCR y los datos de seis idiomas están incluidos; no hace falta instalar Tesseract. OCR se ejecuta íntegramente en tu equipo; diseños complejos y columnas necesitan revisión humana.

Límites actuales: archivo 150 MiB, contenido expandido ZIP 200 MiB, mensaje JSON 900.000 bytes, extracción web 200.000 caracteres. No se ejecutan macros, scripts ni HTML extraído. No se indexan documentos por Internet.

## Extensión: Chrome, Chromium, Edge, Brave y Firefox

```sh
npm run build
```

Se generan dos distribuciones con la misma base:

- `apps/browser-extension/dist/chromium`: abre `chrome://extensions`, activa modo desarrollador y carga esta carpeta sin empaquetar. Edge, Brave y otros derivados permiten el flujo equivalente.
- `apps/browser-extension/dist/firefox`: carga `manifest.json` desde `about:debugging → Este Firefox → Cargar complemento temporal`. El manifest requiere Firefox 140+; la distribución permanente requiere firma de Mozilla.

Después abre **Ajustes → Escucha desde tu navegador**: pega el ID Chromium y pulsa Registrar, o pulsa Registrar Firefox. También puedes registrar desde terminal. Para Chromium copia el ID que muestra la página de extensiones:

```sh
uv run python scripts/register_native_host.py --chromium-id aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

**Sustituye el ID de ejemplo por el real.** El script detecta perfiles existentes en Linux/macOS, genera los manifests y no sobreescribe un registro distinto. Puedes indicar un navegador aunque todavía no tenga perfil:

```sh
uv run python scripts/register_native_host.py --browser firefox
uv run python scripts/register_native_host.py --browser chromium --chromium-id TU_ID_REAL
```

Zen Browser utiliza la distribución Firefox y, en Linux, busca el host en
`~/.mozilla/native-messaging-hosts/org.lector.local.json`. Si el popup indica que
no encuentra el motor local, registra el host mediante **Registrar Firefox** o
el comando anterior para Firefox y pulsa **Reintentar conexión**. Cargar la
extensión temporal no registra el host. Para usar el ejecutable empaquetado desde
este proyecto:

```sh
.venv/bin/python -m reader_core install-host --browser firefox --host artifacts/core/lector-core
```

En Windows se requiere el ejecutable empaquetado:

```powershell
uv run python scripts/register_native_host.py --host artifacts/windows/core/lector-core/lector-core.exe --chromium-id TU_ID_REAL
```

El registro es por usuario. No necesitas editar JSON ni el registro de Windows. `--output artifacts/manifests` permite generar y revisar todo sin modificar la configuración del sistema. `--replace` autoriza sustituir un registro previo de **Lector Local**; nunca modifica otros nombres de host.

Uso: selecciona texto → botón derecho → **Leer selección**. También están disponibles **Leer artículo**, **Leer desde aquí…**, **Pausar/reanudar** y **Detener**. «Leer desde aquí» activa un cursor y espera que pulses un párrafo; Escape cancela. El popup ofrece los mismos controles de voz, idioma y velocidad que el escritorio. No necesitas abrir la GUI: el host inicia el core compartido si todavía no está funcionando.

No se solicita `<all_urls>`. La inyección utiliza `activeTab` tras una acción del usuario. Por eso el botón flotante opcional solo funciona en páginas donde has activado previamente el lector y no aparece automáticamente en todas las webs. Páginas internas del navegador y algunas vistas de PDF bloquean la inyección; abre el PDF en el escritorio.

La compatibilidad de código y manifests está preparada para ambos motores de navegador. La instalación manual en navegadores reales tiene un [checklist](docs/testing.md); no se afirma certificación en cada navegador/SO sin ejecutar esa prueba.

## Voz y dispositivos

Kokoro-82M ONNX es el motor predeterminado. Incluye las voces españolas **Dora (`ef_dora`)**, **Alex (`em_alex`)** y **Santa (`em_santa`)**. También se ofrecen voces inglesa, francesa, italiana y portuguesa. Seleccionar idioma manual cambia a una voz compatible. «Según la voz» usa el idioma de la voz; no pretende detectar automáticamente el idioma de cada párrafo.

CPU es el modo garantizado por el adaptador. Auto usa CUDA si el runtime instalado ofrece el proveedor CUDA y vuelve a CPU si falla. La instalación predeterminada incluye `onnxruntime` CPU; CUDA requiere un entorno preparado con `onnxruntime-gpu` y sus bibliotecas correspondientes. MPS no está disponible en este adaptador ONNX y aparece deshabilitado; Apple Silicon puede usar CPU. No se afirma aceleración Metal implementada.

Piper se incluye en el ejecutable con la voz española `es_ES-sharvard-medium`. Selecciona «Piper · español» en el selector. Una importación completa en `models/piper/piper_es.onnx` y `piper_es.onnx.json` permite sustituir la voz incluida. El build prepara y verifica los recursos con `scripts/prepare_assets.py`; consulta [recursos incluidos](docs/bundled-resources.md). `lector-core self-test` verifica audio de ambos motores y OCR con red bloqueada y almacenamiento vacío.

El diccionario de pronunciación está preparado en ajustes del protocolo: `{ "pronunciation": { "SQL": "ese cu ele" } }`. Aún no tiene editor visual. Las preferencias TTS pertenecen al core, no a cada interfaz.

## Privacidad y almacenamiento

Los documentos se mantienen en memoria mientras están abiertos; el progreso guarda su hash, ruta y posición en SQLite. La caché sí contiene audio del texto leído, en WAV. Puedes vaciarla desde Ajustes o Privacidad. No hay cifrado de base de datos ni audio: protege tu cuenta y tu disco si trabajas con material sensible.

Directorio por defecto:

| Sistema | Directorio |
|---|---|
| Windows | `%LOCALAPPDATA%/LectorLocal` |
| macOS | `~/Library/Application Support/LectorLocal` |
| Linux | `$XDG_DATA_HOME/lector-local` o `~/.local/share/lector-local` |

`LECTOR_DATA_DIR` permite elegir un directorio. No ejecutes la aplicación como administrador/root. Las interfaces y el modelo deben usar el mismo directorio para compartir estado. El core sigue disponible cuando la GUI se cierra; solo admite una lectura activa. No se instala autostart ni auto-update.

Native Messaging transporta JSON con framing nativo. El host y el escritorio acceden a un canal TCP **solo en 127.0.0.1**, con puerto aleatorio y token de 256 bits en un archivo privado. No es HTTP, no es accesible por webs y no escucha en LAN. Consulta [seguridad](docs/security.md).

## Desarrollo y pruebas

```sh
uv run python scripts/verify.py
# Comprobación nativa, después de empaquetar el core:
cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --check
# Síntesis española real con acceso de red bloqueado en el test:
LECTOR_TEST_REAL_TTS=1 uv run pytest tests/test_tts_offline.py -q
# Prueba que emite audio por los altavoces:
LECTOR_DATA_DIR="$PWD/.runtime" uv run python scripts/smoke_audio.py
```

Los resultados ejecutados en esta entrega están en [verificación](docs/verification.md).

Las pruebas ordinarias usan un TTS y salida de audio simulados, con integración TXT → cola, framing Native Messaging → daemon, autenticación, estado compartido y persistencia. La salida simulada nunca se activa como fallback de producción. Las pruebas IPC necesitan permiso para crear sockets loopback si tu entorno está aislado.

El núcleo también funciona sin interfaz:

```sh
printf '%s' '{"protocol_version":1,"id":"demo","type":"command","command":"state","payload":{}}' | uv run python -m reader_core request
```

El comando `speak_text` recibe `text`, `title` opcional y `start_paragraph` opcional. Para elegir voz, idioma y velocidad, usa primero `settings`. Consulta [protocolo](docs/protocol.md).

## Empaquetado

```sh
uv run python scripts/package_core.py
npm run desktop:build
```

PyInstaller genera el core y Tauri lo incorpora como sidecar. Para producir las entregas completas ejecuta `uv run python scripts/build_release.py` en el SO nativo: Windows produce NSIS por usuario; macOS APP/DMG por arquitectura; Linux DEB y TAR portátil. La matriz de [CI](.github/workflows/installers.yml) genera esas versiones en runners nativos cuando se ejecuta en GitHub. Consulta [instaladores y firma](installers/README.md) y [validación manual](docs/manual-validation.md). Hay hooks Windows de registro/retirada; macOS registra desde Ajustes tras copiar la app a Aplicaciones. Las entregas actuales no tienen firma de editor.

Construir en una distribución Linux moderna no garantiza compatibilidad con sistemas de glibc más antiguos. Las releases deben usar una imagen de compilación con la glibc mínima soportada. No se requiere Docker para ejecutar Lector Local.

## Resolución de problemas

- **Modelo ausente:** instálalo en Ajustes o copia ambos archivos al destino mostrado. No hay descarga durante Play.
- **Modelo corrupto:** ejecuta el instalador; verifica SHA-256 y reemplaza archivos que no coinciden.
- **Host no encontrado:** confirma el nombre `org.lector.local`, el ID de extensión, ruta absoluta y permisos de ejecución. Recarga la extensión después del registro.
- **Core incompatible:** escritorio, host y extensión deben utilizar protocolo v1.
- **Sin audio:** comprueba la salida predeterminada del sistema. PortAudio puede bloquearse en un sandbox sin acceso a PipeWire/PulseAudio; ejecuta como usuario normal fuera de ese aislamiento. El core carga el backend al reproducir, no durante la extracción.
- **PDF escaneado:** activa OCR en Ajustes. Los datos de español y el motor vienen incluidos.
- **CUDA:** vuelve a CPU o instala un runtime compatible. La selección manual de MPS se rechaza expresamente.
- **Firefox/Chromium en Flatpak/Snap:** los hosts nativos pueden requerir un portal o instalación fuera del aislamiento; usa primero una instalación convencional.
- **Linux AppImage:** revisa FUSE y permisos de ejecución.

Los logs son locales y no incluyen texto de documentos ni fonemas. `LECTOR_LOG_LEVEL` admite INFO, DEBUG o ERROR; los fallos registran tipo y ubicaciones técnicas, sin valores del contenido. El core de producción no envía datos a servicios externos. Las descargas explícitas de modelos y la instalación de dependencias sí requieren Internet.

## Licencias

El código propio está bajo MIT. **Esto no relicencia las dependencias ni los modelos.** Kokoro-82M: Apache-2.0; kokoro-onnx: MIT; ONNX Runtime: MIT; Readability: Apache-2.0; Tauri: MIT/Apache-2.0; Piper actual: GPL-3.0, con licencias por voz. PyMuPDF/MuPDF y phonemizer introducen obligaciones GPL/AGPL en la distribución; revisa [licencias](docs/licenses.md) antes de comercializar o empaquetar. El uso comercial no equivale a permiso para cerrar el código de las dependencias copyleft.
