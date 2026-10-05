# Auditoría técnica — 0.2.0

Se conserva la arquitectura React/TypeScript + Tauri + Python y la extensión MV3. Se aplicaron cambios incrementales sobre el proyecto existente.

## Cambios comprobados

- Manifest común con overrides Firefox/Chromium, iconos 16/32/48/128 y versión de package.json. Se elimina storage, que no se utilizaba. No hay permisos permanentes de sitios.
- IDs y host centralizados en distribution.json. Firefox mantiene lector-local@lector.local; producción Chromium espera ID de tienda y desarrollo tiene clave pública fija. Sin comodines.
- Limpieza del directorio dist antes del build para retirar bundles antiguos. ZIP determinista y paquete de fuentes AMO reconstruido en un directorio aislado, con comparación byte por byte.
- Firefox declara websiteContent por envío al programa local. Chrome conserva mensajes de error nativo. Desconectar limpia estado y solicitudes pendientes; detener o finalizar retira resaltado.
- PyInstaller onedir en todos los sistemas; recursos localizados mediante Tauri. Se elimina extracción completa en cada petición Linux. Se conservan modelos ONNX cargados en el daemon.
- Primer fragmento limitado a 100 caracteres; síntesis actual antes del prefetch, ventana limitada y cancelación de solicitudes obsoletas. Caché basada en contenido de modelos, voz, idioma, velocidad, pronunciación y normalización, con límite incluso para fragmentos sobredimensionados.
- Pesos TTS separados del build: descarga explícita desde Ajustes, HTTPS, tamaño/SHA-256 y reemplazo por directorio con rollback. Bloqueo de sistema operativo recuperable al terminar el proceso. Un catálogo JSON único para Kokoro y Piper.
- Runtime Windows incluye MSVC y el instalador WebView2 offline. El host se registra por usuario; instalador Windows lo retira al desinstalar. Firefox/Zen se registra aunque aún no exista .mozilla.
- Lockfile universal con wheels macOS Intel y Apple Silicon; Node 22 aislado para validación y min macOS 14. CI y publicador de artefactos GitHub separados de la publicación en tiendas.

## Eliminaciones

Después de revisar referencias, se eliminaron package_source.py (sustituido por el paquete específico AMO), package_testers.py (sustituido por release.py), preview_ui.py (capturas reales) y el icono 64 no referenciado. SilentOutput se mueve a tests/helpers.py. Se retira @vitejs/plugin-react sólo del workspace de extensión, donde no se usaba; se conserva donde el escritorio lo necesita. Piper no incorpora los archivos de entrenamiento. No se eliminan Readability ni webextension-polyfill: ambos tienen uso real.

## Evidencia y límites

50 tests Python y 4 tests web pasan. Ruff, MyPy, TypeScript, ESLint, comprobación de versiones y npm audit pasan. El validador Mozilla no tiene errores; conserva cuatro avisos documentados sobre helpers DOM de React/Readability. El código propio no usa innerHTML ni dangerouslySetInnerHTML.

Zen: perfil aislado, error de host ausente, registro/reintento, estado/preferencias, daemon compartido, rechazo de archivos desde navegador y voz real con pausa/reanudación/detener. Chromium 153: bundle de producción, host ausente, Native Messaging al runtime empaquetado, preferencias y popup sin page errors. Su prueba automatizada no simula el gesto activeTab para extracción de Wikipedia; la extracción se comprueba con tests DOM y las acciones deben repetirse manualmente en cada navegador.

Linux: self-test empaquetado con red bloqueada, Kokoro/Piper reales y OCR; audio real por Native Messaging. Windows: instalación silenciosa y registro en Wine, self-test del core instalado y OCR. WebView2 real, interfaz y desinstalación Windows requieren tester nativo. Los DMG y los instaladores nativos sólo se ofrecen cuando CI termine satisfactoriamente; una build CI no demuestra validación manual de audio/interfaz macOS.

Medición local Linux, tres ejecuciones de --help: mediana anterior onefile 2.637 s; onedir 0.098 s. Esta medición evalúa arranque del ejecutable, no latencia completa de voz. El instalador Windows inicial ocupaba 733 MB y el actual alrededor de 333 MB; Linux inicial 549 MB y build Ubuntu actual alrededor de 182 MB. El ZIP de extensión anterior ocupaba 324 KB y el actual aproximadamente 109 KB. Los tamaños/SHA-256 exactos están en la Release; pueden cambiar con el build nativo final.

Pendientes de distribución oficial: certificados Windows/Apple, notarización, firma AMO, ID Chrome Web Store, políticas/contactos públicos y cumplimiento de fuentes de componentes copyleft. SIGNING_REQUIRED se declara en la entrega. No se afirma firma o aceptación por tiendas.
