# Envío a AMO y firma Firefox / Zen

1. Abrir [AMO Developer Hub](https://addons.mozilla.org/developers/) y elegir una extensión nueva.
2. Elegir distribución listada en AMO o no listada para testers.
3. Subir `release/extensions/lector-local-0.2.2-firefox.zip` como extensión.
4. Subir `lector-local-0.2.2-firefox-source.zip` como fuentes. Copiar las instrucciones de `FIREFOX_BUILD.md`. El ZIP de fuentes reconstruye exactamente el bundle con npm ci.
5. Completar descripción, política pública, contacto y notas de `store/firefox/` y `store/chrome/`. Mantener ID `lector-local@lector.local` en toda actualización.
6. Declaración requerida: `websiteContent` por envío de texto/títulos al host nativo local. Firefox escritorio mínimo 140; seleccionar únicamente plataformas de escritorio en AMO. El límite Gecko Android 142 evita avisos sobre la declaración moderna, pero no ofrece soporte Android: no hay app nativa Android. Véase [consentimiento oficial](https://extensionworkshop.com/documentation/develop/firefox-builtin-data-consent/).
7. Descargar el `.xpi` firmado después de validación/revisión. Compartirlo e instalar mediante about:addons > Instalar complemento desde archivo. Zen depende de su versión Gecko y políticas de firma; comprobar con el XPI firmado.

El ZIP generado aquí está sin firmar: SIGNING_REQUIRED. Puede cargarse temporalmente desde about:debugging > Este Firefox > Cargar complemento temporal, eligiendo manifest.json del ZIP extraído. Desaparece al reiniciar. Cambiar extensión de .zip a .xpi no lo firma.

[Fuentes para revisión](https://extensionworkshop.com/documentation/publish/source-code-submission/).

El linter registra cuatro avisos UNSAFE_VAR_ASSIGNMENT en helpers de React/Readability incluidos en el bundle. El código propio no usa innerHTML ni dangerouslySetInnerHTML: Readability trabaja sobre un clon y el HTML se analiza en un documento inerte; React representa texto escapado. scripts/lint_extension.py conserva el informe completo y rechaza otros avisos/errores.
