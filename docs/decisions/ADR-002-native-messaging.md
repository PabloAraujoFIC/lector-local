# ADR-002: Native Messaging con core único

Aceptado. La extensión comunica por Native Messaging con un host local; manifests diferentes para Chromium (`allowed_origins`) y Firefox (`allowed_extensions`), lógica compartida.

Un host por conexión no debe crear un reproductor independiente. Se elige un daemon local único protegido por lock del SO. Host y desktop comparten IPC JSON autenticado sobre 127.0.0.1 con puerto aleatorio. No se utiliza HTTP, no se escucha en LAN y no se publica API accesible por páginas. El token queda en un archivo privado del usuario y no llega al navegador.

El daemon se separa del ciclo de vida de la GUI/host. Windows requiere breakaway del job del navegador; comprobar el comportamiento en la matriz nativa. PyInstaller necesita reiniciar su entorno al lanzar un proceso independiente para que no dependa del directorio temporal del host padre.

Fuentes: [Native Messaging Mozilla](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_messaging), [manifest nativo](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Native_manifests).
