# Verificación y modo offline

## Automatizada

- Python: extractores TXT/PDF/ODT/DOCX/EPUB/HTML/MD/RTF, PDF cifrado/escaneado, Unicode, abreviaturas, offsets, caché, SQLite, protocolo inválido, framing, tamaño, settings atómicos, cola con mock, pausa/reanudación, seek, autenticación IPC y estado compartido de cliente desktop/browser.
- Native Messaging: proceso real recibe framing desde stdin y actualiza el daemon compartido; tests cubren argumentos de lanzamiento Chromium y Firefox. `scripts/smoke_native.py --host artifacts/core/lector-core` comprueba audio real, autoarranque y supervivencia al desconectar el host.
- TypeScript: Readability, eliminación de navegación/scripts/ocultos, leer desde párrafo y protocolo.
- Comprobaciones: Ruff, mypy, TypeScript, ESLint y builds Vite.
- Optativa: `LECTOR_TEST_REAL_TTS=1` sintetiza español con los modelos instalados y bloquea conexiones Python HTTP y socket de salida durante síntesis. No reemplaza una captura de tráfico nativo del SO.

## Checklist offline manual

1. Instalar dependencias, modelo y extensión; registrar el host con ID correcto.
2. Abrir una página con un artículo y mantenerla cargada.
3. Desconectar Wi-Fi/Ethernet. No cerrar la página.
4. Arrancar escritorio y abrir TXT; Play debe emitir voz española sin descarga.
5. Pause, Resume y Stop; cambiar velocidad y voz.
6. Cerrar GUI. Seleccionar texto del artículo cargado, menú «Leer selección»; debe sonar sin GUI.
7. Abrir GUI durante la lectura y pausar allí; la extensión debe reflejar la pausa.
8. Leer artículo y «Leer desde aquí»; comprobar texto sin menús/anuncios.
9. Cerrar y reabrir el documento; debe continuar en el punto guardado.
10. Revisar conexiones salientes con herramienta del SO; el core no debe abrir conexiones a Internet. IPC loopback es esperado.
11. Quitar temporalmente el modelo y pulsar Play: mostrar error, nunca intentar descargarlo.
12. PDF con texto, escaneado con OCR y archivo corrupto: probar sin Internet.

## Matriz que debe completarse antes de una release

Windows 11: Chrome, Edge, Brave, Firefox; macOS Apple Silicon: Chrome/Firefox, CPU; Linux: Chromium/Chrome/Brave/Firefox. Probar instalador, registro y desinstalación, permisos, audio, suspensión del equipo y daemon independiente. Usar perfiles de pruebas sin credenciales; los manifests permiten únicamente el ID instalado.

## Calidad de voz

La muestra `artifacts/prueba-espanol.wav` verifica inferencia real en español. Para evaluación perceptiva compara varias voces sobre: números/fechas, abreviaturas, preguntas, nombres propios, párrafos largos y lectura de 30 minutos. Registra velocidad, dispositivo, tiempo de síntesis y preferencia subjetiva. No se afirma calidad comparable a servicios comerciales a partir de un único WAV.
