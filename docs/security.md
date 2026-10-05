# Privacidad y seguridad local

No hay listeners en LAN, servicios externos de síntesis, telemetría de aplicación ni clientes de IA. El único módulo que realiza descargas es `model_manager`, ejecutado tras aceptación. ONNX Runtime desactiva explícitamente eventos de telemetría antes de crear sesiones. Las variables de Hugging Face se fuerzan a offline y sin telemetría, aunque el adaptador actual no usa Hugging Face.

## Fronteras de confianza

1. La web es entrada no confiable. Readability se ejecuta en la extensión, sobre un clon. Se envía texto, no HTML ejecutable. No hay `eval`, `new Function` ni HTML insertado con `dangerouslySetInnerHTML`.
2. Los scripts de contenido solo se inyectan después de una acción autorizada mediante `activeTab`. Mensajes de scripts de contenido solo pueden solicitar lectura de texto. Controles generales proceden del popup de la propia extensión.
3. El host valida versión, tamaño, tipo, comandos y parámetros. El origen navegador no puede solicitar archivos locales. Los manifests autorizan un ID preciso, nunca todas las extensiones.
4. IPC enlaza solo `127.0.0.1` con puerto aleatorio. Cada conexión exige un token criptográfico de 256 bits. JSON no se deserializa con pickle. Una web no puede obtener el token ni acceder al canal mediante HTTP/WebSocket.
5. En Unix el directorio se crea con modo 0700 y el archivo token con 0600. En Windows se usa LOCALAPPDATA y las ACL heredadas de la cuenta. Un proceso malicioso ejecutado por el mismo usuario puede acceder a datos y token: esa amenaza requiere aislamiento del SO y no la resuelve un secreto en disco.
6. ZIP/XML/documentos tienen límites de tamaño y no se extraen a rutas arbitrarias. XML DTD/entidades se rechazan en formatos ofimáticos. No se ejecuta shell con parámetros del navegador.

## Permisos de la extensión

| Permiso | Motivo |
|---|---|
| contextMenus | Leer selección/artículo y controlar reproducción desde menú |
| activeTab | Acceso temporal a la pestaña tras una acción del usuario |
| scripting | Inyectar extractor local y botón opcional en esa pestaña |
| nativeMessaging | Conectar exclusivamente con `org.lector.local` |
| storage | Reservado para preferencias de UI/instalación; preferencias TTS viven en el core |

No se requiere `<all_urls>`, `tabs` para acceso general, `webRequest` ni acceso a cookies. No existe un content script global. El botón flotante funciona solo tras activar una página; esto evita permisos permanentes sobre todas las páginas.

## Almacenamiento y límites

SQLite contiene rutas, posición y preferencias. La caché contiene voz sintetizada y puede revelar contenido. Ni caché ni base de datos se cifran. La eliminación de archivos no garantiza borrado forense de SSD ni de backups. El documento completo vive en memoria y no se escribe al log.

Mensajes 900 KB, documentos 150 MiB y ZIP expandido 200 MiB. Estos límites reducen ataques de memoria; no constituyen un sandbox de parsers ni impiden que otro proceso del mismo usuario abuse del host. PDF/OCR usan bibliotecas nativas que deben mantenerse actualizadas.

Los hashes del modelo se fijaron a partir de los archivos de la release oficial de kokoro-onnx por HTTPS el 5 de octubre de 2026. Detectan corrupción y cambios posteriores; no son una firma independiente del autor. No existe auto-update. Las releases futuras necesitan artefactos firmados, permisos del instalador revisados y auditoría de dependencias.
