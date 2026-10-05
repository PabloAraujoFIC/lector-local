# Guía para testers — 0.2.0

Enviar el instalador de su sistema y el ZIP de su navegador desde release/. Enviar también esta guía y SHA256SUMS.txt. No necesita instalar Python, Piper, Kokoro, npm ni Rust. Necesita Internet una vez para descargar una voz y el navegador instalado.

## Windows x64

1. Ejecutar el archivo `*-setup.exe` de release/desktop/windows. Es una entrega unsigned: sólo continuar tras verificar remitente y checksum. WebView2 se instala desde el instalador offline incluido si falta.
2. Abrir Lector Local desde Inicio. Ajustes > Descargar Piper o Kokoro. Esperar la verificación.
3. Instalar la extensión siguiendo los pasos de abajo. En Chromium registrar su ID desde Ajustes.
4. Probar lectura y desinstalar desde Aplicaciones instaladas. Confirmar retirada del registro del host.

## Linux x64

1. En Ubuntu 22.04 o posterior, Debian 12 o posterior y sistemas compatibles con glibc ≥ 2.35 y WebKitGTK 4.1, instalar el `.deb`: `sudo apt install ./lector-local-0.2.0-linux-x64.deb`. apt resuelve bibliotecas del sistema como WebKitGTK; Python y motores vienen incluidos.
2. Abrir Lector Local desde el menú. Descargar una voz en Ajustes.
3. Para Arch u otras distribuciones, usar el tar portátil si se incluye en la entrega; descomprimir y ejecutar lector-local-desktop dentro de la carpeta, conservando core/ a su lado. El tar publicado de CI requiere glibc 2.35 o posterior y WebKitGTK 4.1/GTK3, ALSA y PortAudio del sistema (en Arch: webkit2gtk-4.1, gtk3, alsa-lib, portaudio y pipewire-alsa). El build local de Arch requería glibc 2.44 y ha sido sustituido por el build Ubuntu para distribución. Las dependencias exactas se indican en el reporte de build. No existe AppImage validada en esta entrega.
4. Abrir el navegador al menos una vez y volver a abrir Lector Local para registrar el host. Añadir la extensión.

## macOS 14 o posterior · Intel / Apple Silicon

1. Descargar de la Release el DMG correspondiente a su arquitectura: arm64 para Apple Silicon o x64 para Intel.
2. Abrir DMG y arrastrar Lector Local a Aplicaciones; iniciar desde allí.
3. Si el sistema bloquea la entrega unsigned, el tester decide si permite abrirla en Privacidad y seguridad después de verificar origen/checksum. No es una entrega notarizada.
4. Descargar una voz en Ajustes, instalar extensión y probar. Al quitar la app, retirar sus registros Native Messaging si ya no se usa.

## Chrome, Chromium, Edge y Brave

1. Descomprimir `lector-local-0.2.0-chrome.zip` en una carpeta permanente.
2. Abrir chrome://extensions (Edge: edge://extensions; Brave: brave://extensions). Activar Modo desarrollador y Cargar desempaquetada. Seleccionar la carpeta con manifest.json.
3. Copiar ID. En escritorio, Ajustes > Escucha desde tu navegador, pegar ID y registrar. El ID de esta carga puede variar; el ID de producción se fijará al crear la ficha Chrome Web Store.
4. Visitar Wikipedia, seleccionar un párrafo, menú contextual Leer selección. Probar popup Leer artículo, pausa, volumen, voz, párrafos y detener. Páginas internas del navegador no permiten inyección.

## Firefox y Zen (Gecko 140+)

1. Descomprimir `lector-local-0.2.0-firefox.zip`.
2. Abrir about:debugging > Este Firefox > Cargar complemento temporal. Elegir manifest.json. Aceptar websiteContent para el envío al programa local. No sale texto del equipo.
3. Abrir escritorio > Ajustes > Registrar Firefox si no se detectó automáticamente. Reintentar conexión en popup.
4. Probar Wikipedia y controles. La instalación temporal desaparece al reiniciar. Para instalación persistente, el desarrollador debe entregar un XPI firmado por AMO; renombrar ZIP no añade firma.

## Pruebas que comunicar

Indicar SO/arquitectura/versión de navegador, instalador usado, host conectado, primera descarga de voz, audio, documento TXT/PDF/RTF y PDF escaneado con OCR, pausa/seek/fin, segunda lectura con caché y prueba sin Internet después de descargar. Adjuntar errores sin texto privado. macOS/Windows nativos deben confirmarse con testers: Wine y un build CI no sustituyen esa validación.
