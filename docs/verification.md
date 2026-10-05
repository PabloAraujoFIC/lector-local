# Verificación de esta entrega

Entorno: Linux x86_64 (CachyOS/Arch), Python 3.12.15 aislado, Node 26.1.0, Rust 1.98.1. Fecha: 5 de octubre de 2026.

Resultados ejecutados:

- **45 pruebas Python aprobadas**, incluyendo síntesis Kokoro real con bloqueo de conexiones Python de salida. Sin skips cuando `LECTOR_TEST_REAL_TTS=1`.
- **4 pruebas TypeScript aprobadas**: Readability, contenido oculto, lectura desde párrafo y protocolo.
- Ruff, mypy, TypeScript y ESLint: sin errores.
- Build de escritorio web y extensión Chromium/Firefox: correcto.
- `cargo check`, `cargo build` y `cargo fmt --check`: correctos.
- PyInstaller: ejecutable `artifacts/core/lector-core`, con datos de fonemización y eSpeak NG incluidos.
- Tauri: paquete DEB de Linux construido en `apps/desktop/src-tauri/target/release/bundle/deb/`.
- Síntesis española real: 6,31 s de WAV a 24 kHz en 2,78 s de CPU en la primera prueba; muestra en `artifacts/prueba-espanol.wav`.
- Reproducción real: Play → Pause → Resume → Finished aprobada en `scripts/smoke_audio.py`.
- Host empaquetado: Native Messaging → inicio automático del core → audio español → pausa visible desde cliente desktop → desconexión del host → reanudación desde desktop → finalización aprobada en `scripts/smoke_native.py`.
- Argumentos de lanzamiento de Chromium y Firefox cubiertos por tests de Native Messaging reales.
- App Tauri arrancada con el directorio `.runtime` y documento `examples/bienvenida.txt` cargado en el core. Vista visual revisada con snapshot WebKit, guardada en `artifacts/desktop-preview.png`; esa vista utiliza un snapshot del estado, no controla audio.
- Auditoría npm después de actualizar Vitest: cero vulnerabilidades reportadas en la consulta realizada.

Los primeros tests IPC fallaron dentro del sandbox por bloqueo de sockets locales. Se ejecutaron correctamente con acceso loopback fuera de ese aislamiento. PortAudio se carga al reproducir: los tests simulados y la extracción no dependen de inicializar un dispositivo de audio.

Zen 1.22.1b (Gecko 155) se ha validado con perfil temporal: extensión Gecko real, panel conectado, Native Messaging, preferencias compartidas con cliente desktop, rechazo de acceso a archivos, voz española y clics reales Pausar/Reproducir/Detener. Evidencia en `artifacts/zen-validation.json`. Chromium, menús contextuales/activeTab y Windows/macOS siguen pendientes. No se certifican CUDA, MPS, Piper, OCR con todas las distribuciones ni escucha subjetiva prolongada. La prueba offline automatizada bloquea salidas Python; la captura de tráfico nativo y el checklist con Internet físicamente desconectado siguen siendo pruebas manuales de release.

Actualización de empaquetado: configuraciones nativas NSIS y DMG, hooks Windows por usuario, retirada conservadora del registro y scripts de firma/verificación añadidos. La suite final con `LECTOR_TEST_REAL_TTS=1` arroja 45 passed; los nuevos tests cubren que la retirada conserva registros reemplazados o malformados. El flujo de firma y la matriz de runners todavía no se han ejecutado.
