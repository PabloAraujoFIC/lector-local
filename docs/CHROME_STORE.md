# Envío a Chrome Web Store

1. Crear o abrir una ficha en el [panel oficial](https://chrome.google.com/webstore/devconsole), con cuenta de desarrollador habilitada.
2. Subir únicamente `release/extensions/lector-local-0.2.2-chrome.zip` como paquete. No subir el código fuente Firefox ni el instalador.
3. Copiar el ID de 32 letras asignado. Fijar `production.chromiumId` en `core/reader_core/distribution.json`; reconstruir instaladores para registro automático. Para testers anteriores, registrar ese ID desde Ajustes. Nunca usar comodines ni el ID de desarrollo para autorizar producción.
4. Completar descripción, permisos, notas y privacidad desde `store/chrome/`. Publicar política HTTPS y enlaces accesibles de descarga; añadir contacto de soporte.
5. Añadir capturas reales de 1280×800 o 640×400 e icono 128×128. Las capturas de pruebas están en `store/chrome/screenshots/` cuando se hayan generado; revisarlas antes de subir. No afirmar compatibilidad de un sistema pendiente de validar.
6. Completar declaración de manejo local de texto y dependencia de aplicación externa. Revisar y enviar manualmente. No se publica mediante CI.

El ZIP de producción no contiene `key`, ID de desarrollo ni firma CRX. La tienda firma y distribuye. Los builds development usan clave pública fija, con ID diferente, para carga desempaquetada.

[Flujo oficial de publicación](https://developer.chrome.com/docs/webstore/publish).
