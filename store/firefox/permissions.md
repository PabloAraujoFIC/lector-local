# Justificación de permisos

| Permiso | Uso |
|---|---|
| activeTab | Acceso temporal a la pestaña al pedir leer. |
| scripting | Inyectar el extractor y resaltado únicamente en esa pestaña. |
| contextMenus | Mostrar Leer selección, Leer artículo y controles de reproducción. |
| nativeMessaging | Enviar texto y órdenes al motor local org.lector.local. |

No se solicita acceso permanente a sitios, historial, cookies, descargas ni almacenamiento del navegador. No se descarga código remoto. El polyfill proporciona compatibilidad de APIs Promise entre Firefox y Chromium.
