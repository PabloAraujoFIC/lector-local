# Política de privacidad — Lector Local

Actualizada el 5 de octubre de 2026, versión 0.2.0.

Cuando eliges Leer selección o Leer artículo, la extensión extrae el texto y título y los envía mediante Native Messaging a Lector Local en tu ordenador. No envía URLs, historial, cookies ni texto a Internet. En Firefox se declara `websiteContent`: Mozilla considera transmisión cualquier manejo fuera del navegador, incluido un programa nativo local. La instalación solicita aceptar esa declaración.

El escritorio conserva preferencias, progreso y documentos en SQLite y audio en una caché limitada en el directorio local de datos del usuario. Puedes vaciar la caché desde Ajustes. Puedes eliminar el directorio de datos al desinstalar si deseas retirar todo el historial. No hay analytics, cuentas, publicidad, venta de datos ni telemetría propia. Se desactivan eventos de telemetría ONNX Runtime.

Sólo al pulsar Descargar en Ajustes, el escritorio se conecta por HTTPS a GitHub y sus servidores de archivos para Kokoro, o a Hugging Face y sus servidores de archivos para Piper. Esos proveedores reciben la información ordinaria de una conexión HTTP, incluida la dirección IP. Nunca reciben el documento. Los modelos se verifican con tamaño y SHA-256 antes de instalarlos. Una vez descargados, la síntesis y OCR funcionan sin conexión.

El navegador y sistema operativo pueden realizar sus propias conexiones ajenas a Lector Local. Para consultas, usar el contacto de soporte publicado en la ficha de la tienda. El responsable deberá publicar este documento en una URL pública e indicar su contacto antes de distribuir oficialmente.

Referencia: [consentimiento de Firefox](https://extensionworkshop.com/documentation/develop/firefox-builtin-data-consent/).
