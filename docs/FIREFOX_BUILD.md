# Reconstrucción para Mozilla AMO

Versión 0.2.2. Node.js 22.x y npm 10.x. No se necesita Python, Rust, modelos ni aplicación de escritorio para reconstruir la extensión.

1. Descomprimir `lector-local-0.2.2-firefox-source.zip` en un directorio vacío.
2. Ejecutar `npm ci` en ese directorio, sin cambiar el lockfile.
3. Ejecutar `npm run build:extension:firefox`.
4. El resultado está en `apps/browser-extension/dist/firefox/`. Comparar cada archivo con el ZIP de Firefox remitido a AMO. Los archivos del bundle son deterministas; los ZIP oficiales fijan fecha y permisos de sus entradas.

Vite construye el popup React; esbuild empaqueta background y content script. El código usa Readability y webextension-polyfill, incluidos localmente. No hay código remoto, ofuscación, mapas ni descargas de modelos en la extensión. El ID Gecko procede de `core/reader_core/distribution.json` y la versión de `package.json`. Ambos se incluyen en este paquete. `npm run build:extension:chrome` genera también la variante Chromium.

La extensión requiere Lector Local instalado para leer. Esto no afecta a su reconstrucción. Véase la [documentación oficial de fuentes](https://extensionworkshop.com/documentation/publish/source-code-submission/).
