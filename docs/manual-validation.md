# Prueba de aceptación en Windows y macOS

Registra SO/arquitectura, versión de navegador, nombre y SHA-256 del instalador, resultado y cualquier mensaje exacto de error. Estas pruebas están pendientes; ningún check de CI las sustituye.

1. Instala con usuario estándar, en ruta con espacios y caracteres españoles. Windows: comprueba instalación per-user, acceso directo y desinstalador. macOS: copia la app a Aplicaciones y expulsa el DMG antes de abrirla.
2. Desconecta Internet desde el primer inicio. Abre Ajustes y comprueba que Kokoro y Piper están disponibles sin descargas. Prueba ambos motores con TXT, PDF, DOCX y EPUB y activa OCR para un PDF escaneado. Verifica voz española, pausa/reanudación, parada, volumen, velocidad y navegación.
3. Cierra/reabre la GUI y comprueba preferencias/progreso. Prueba también iniciar desde la extensión con la GUI cerrada; debe arrancar el core y salir voz. Cierra el panel/navegador durante una lectura y comprueba que el core sigue funcionando.
4. Carga temporalmente la extensión en Firefox/Zen o descomprimida en Chromium. Registra desde Ajustes; Chromium necesita el ID real de esa instalación. Prueba selección por menú contextual, artículo con anuncios, «Leer desde aquí», resaltado/autoscroll y los botones del panel. Comprueba que navegador y escritorio muestran el mismo estado y controlan una sola salida de audio.
5. Actualiza/reinstala en la misma ruta y comprueba el registro. Después desinstala: Windows debe retirar el host antes de borrar el core. En macOS ejecuta la retirada indicada en `installers/README.md` antes de eliminar la app. No deben desaparecer modelos/preferencias ni registros de una instalación diferente.
6. Si la entrega está firmada, Windows: `signtool verify /pa /all "instalador.exe"`; macOS: `codesign --verify --deep --strict "/Applications/Lector Local.app"`, `xcrun stapler validate` y `spctl --assess --type execute` sobre esa app. Anota por separado firma, reputación SmartScreen y Gatekeeper. Las entregas actuales carecen de firma de editor.

## Recursos incluidos y prueba offline

El build ejecuta `lector-core self-test` con almacenamiento vacío y conexiones
de red bloqueadas. Comprueba audio real de Kokoro y Piper y reconocimiento OCR
de un PDF escaneado usando exclusivamente los recursos empaquetados.
En Linux, la prueba de reproducción y Native Messaging puede repetirse con:

```sh
.venv/bin/python scripts/smoke_native.py --host artifacts/core/lector-core --bundled --engine piper
.venv/bin/python scripts/smoke_native.py --host artifacts/core/lector-core --bundled --engine kokoro
```

Para validación manual instala en un usuario nuevo, desconecta la red y comprueba
ambos motores y el OCR sin descargar modelos ni instalar Python o Tesseract.

## Zen ejecutado en este equipo

Prueba automatizada con Zen 1.22.1b / Gecko 155, Arch x64, perfil temporal headless. Se cargó el build Gecko de producción sin mocks; el panel conectó por Native Messaging, compartió preferencias con un cliente de escritorio, rechazó comandos de archivos, emitió voz Kokoro española y sus botones reales pausaron, reanudaron y detuvieron. El core sobrevivió a la desconexión del puerto nativo.

La prueba comienza sin registro del host: verifica el aviso con instrucciones para
Zen, ejecuta `install-host --browser firefox` y pulsa **Reintentar conexión** en
el popup. Comprueba que conecta y elimina el error sin reiniciar el navegador.

Evidencia: `artifacts/zen-validation.json`. Repetición (emite audio):

```sh
uv sync --extra dev --extra browser-test --python 3.12 --frozen
uv run --extra browser-test python scripts/smoke_gecko.py --browser /opt/zen-browser-bin/zen-bin --audio
```

El script actualmente aísla registros de Native Messaging solo en Linux. No ha probado los menús contextuales/activeTab de páginas reales, instalación permanente firmada, Chromium, Windows o macOS. El perfil personal de Zen no se modifica.
