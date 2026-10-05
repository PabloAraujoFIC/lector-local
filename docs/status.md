# Estado real de implementación

## Implementado

- Monorepo Tauri 2/React/TypeScript y core Python independiente.
- Protocolo v1, validación, framing Native Messaging y canal compartido autenticado loopback.
- Singleton por directorio con lock del SO, arranque del core desde host sin GUI.
- Kokoro ONNX local con voces españolas, CPU y fallback de CUDA cuando hay proveedor disponible.
- Piper y voz española incluidos, con validación offline de síntesis real en cada build.
- TXT, PDF, ODT, DOCX, EPUB, MD, HTML y RTF; OCR mediante Tesseract opcional.
- Normalización, frases, chunking sin cortar palabras, offsets, síntesis progresiva y buffer limitado.
- Audio único con Play/Pause/Resume/Stop, navegación, velocidad, volumen y progreso.
- Caché WAV con invalidación por modelo y configuración, cuota y limpieza.
- SQLite para preferencias y progreso, reanudación por documento.
- Escritorio con apertura, drag & drop, lectura paginada, resaltado de chunk, autoscroll y Ajustes/Privacidad.
- Extensión compartida con manifests Chromium/Firefox, selección, Readability, lectura desde un clic, popup y botón flotante opcional.
- Instalación explícita de modelos con tamaño, destino, licencia y SHA-256.
- Scripts de empaquetado y registro de hosts multiplataforma, más registro desde Ajustes, sin editar JSON manualmente.
- Pruebas de extractores, protocolo, audio simulado, caché, persistencia, IPC real y extracción web.

## Pendiente de producto

| Funcionalidad | Qué falta / motivo | Siguiente paso |
|---|---|---|
| Compatibilidad validada Windows/macOS | Este entorno es Linux; no se pueden certificar aquí drivers, instaladores y Native Messaging de esos SO | Ejecutar matriz nativa y corregir incidencias |
| Instaladores de producción | NSIS incluye hooks por usuario y retirada con comprobación de propiedad; macOS registra desde Ajustes; falta compilar/probar nativamente y publicar ID Chromium estable | Ejecutar matriz nativa y validar instalación, actualización y retirada |
| Firmas y notarización | Requieren credenciales de distribución | Firmar builds Windows/macOS; publicar extensión Firefox firmada |
| Bandeja y autostart | Opcionales; no se han implementado | Añadir integración Tauri, desactivada por defecto y controles del mismo core |
| MPS/Metal | ONNX elegido no implementa MPS | Añadir adaptador PyTorch o proveedor CoreML probado, manteniendo interfaz TTSEngine |
| Piper real | Motor y voz española sharvard incluidos; prueba offline automática con audio real | Validación perceptiva y nativa en Windows/macOS |
| Idioma automático por texto y alemán Kokoro | Actualmente «auto» sigue idioma de voz; catálogo Kokoro no incluye alemán | Añadir detección local y motor/voz adecuados |
| Calidad perceptiva española | Síntesis real verificable no sustituye escucha comparativa prolongada | Comparar Dora/Alex/Santa y Piper con hablantes nativos |
| PDF de múltiples columnas/tablas | Limpieza y orden actuales son heurísticos | Añadir fixtures de 500 páginas y extracción por regiones |
| Encabezados/secciones/autor completos | Modelo actual agrupa párrafos en sección 0; no extrae toda la semántica de capítulos | Ampliar extractores y modelo Document |
| Resaltado palabra/frase temporizado | Resaltado actual corresponde al chunk, no a tiempos de fonemas | Elegir modelo con duraciones y transportar alineación |
| Seek temporal sin caché | Navegación de ±10 s puede caer en límite de chunk cuando faltan duraciones previas | Persistir índice de duraciones por configuración |
| Cancelación inmediata ONNX/OCR | Se cancela trabajo pendiente y descartan resultados; no se mata inferencia C ya iniciada | Worker de procesos con cancelación dura si la latencia lo exige |
| Historial/biblioteca visual | Un documento activo y progreso guardado; no hay biblioteca de archivos recientes | Añadir historial local sin almacenar contenido sensible |
| Botón flotante global | activeTab limita disponibilidad a páginas activadas | Mantener mínimo privilegio; ofrecer permisos opcionales solo si se solicita |
| Editor de pronunciación | API funcional, sin pantalla de edición | Añadir editor local con validación |
| E2E navegador→altavoces en cada browser | Zen Linux probado con extensión real, Native Messaging, voz española y clics del panel; menús, Chromium y otros SO pendientes | Playwright/WebDriver en perfiles limpios y pruebas manuales de audio |

La app no se presenta como implementación terminada de las 70 secciones originales. Prioriza el flujo local reutilizable y deja los pasos restantes explícitos. No requiere Docker, infraestructura remota ni cuentas.
