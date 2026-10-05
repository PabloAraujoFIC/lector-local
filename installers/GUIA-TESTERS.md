# Lector Local 0.1.0: guía para testers

Cada tester necesita **la aplicación de su sistema operativo**. Para leer páginas
web también necesita **la extensión de su navegador**. La extensión no sustituye
la aplicación: utiliza su motor local. No hay que instalar Python, Piper, Kokoro,
herramientas de desarrollo ni descargar modelos.

## Qué enviar

| Equipo / navegador | Archivo | Estado |
|---|---|---|
| Windows 10/11, Intel/AMD de 64 bits | `windows/lector-local-0.1.0-windows-x64-setup.exe` | Construido; instalación, desinstalación, voces y canal local probados bajo Wine |
| Linux Intel/AMD de 64 bits | `lector-local-0.1.0-linux-x86_64.run` | Instalación, entrada en el menú y voces/OCR comprobados en Arch |
| Ubuntu 24.04 y derivados compatibles / Debian 13 | `Lector Local_0.1.0_amd64.deb` | Alternativa para instalar mediante el gestor de paquetes |
| Linux: ejecución portátil | `lector-local-linux-x86_64.tar.gz` | Alternativa sin instalador |
| macOS Intel | `.dmg` | Pendiente: aún no hay binario construido |
| macOS Apple Silicon (M1/M2/M3/…) | `.dmg` ARM64 | Pendiente: aún no hay binario construido |
| Firefox / Zen | `lector-extension-firefox-unsigned.xpi` | Paquete para carga temporal, sin firma Mozilla |
| Chrome / Chromium / Edge / Brave / Vivaldi | `lector-extension-chromium-unsigned.zip` | Paquete para cargar descomprimido |

Envía también esta guía. No envíes el repositorio, `.venv`, `.bootstrap`, claves
ni un ZIP de fuentes. El mismo paquete de extensión sirve en los distintos SO,
siempre que la aplicación local esté instalada y el navegador se haya registrado.
Las extensiones no se han publicado en las tiendas de Mozilla o Google.

## Windows: instalar la aplicación

1. Guarda el archivo `lector-local-0.1.0-windows-x64-setup.exe` en el equipo.
2. Haz doble clic y sigue el asistente. Elige español si aparece la selección
   de idioma. La instalación es para tu usuario.
3. Es una entrega de pruebas sin firma de editor: Windows puede identificarla
   como aplicación desconocida. Si la política del equipo impide abrirla,
   comunícalo al responsable de la prueba.
4. Abre **Lector Local** desde el menú Inicio.
5. Pega un texto en español y comprueba la lectura. Cambia el motor en Ajustes
   para probar Kokoro y Piper.
6. Si quieres leer páginas, continúa con la sección de Firefox/Zen o Chrome.

El instalador incluye el motor Python, voces/modelos, OCR, bibliotecas de Visual C++
y el instalador offline de WebView2. No borres archivos de su carpeta de instalación.
En Windows se registra Firefox/Zen durante la instalación; Chrome requiere el ID
de la extensión. Para desinstalar: **Configuración → Aplicaciones → Lector Local**.

## Linux: requisitos de esta entrega

Esta compilación es para **x86_64 con glibc 2.39 o posterior**, GTK3 y WebKitGTK 4.1.
No sirve para ARM64, distribuciones basadas en musl, Ubuntu 22.04 ni Debian 12.
La aplicación se construyó en Arch; no se ha validado en todas las distribuciones.
El instalador `.run` comprueba las bibliotecas que necesita antes de instalar.

En Ubuntu/Debian compatibles, `apt` resuelve las dependencias del `.deb`. En Arch,
si faltan las bibliotecas de escritorio, instala los paquetes del sistema:

```sh
sudo pacman -S --needed gtk3 webkit2gtk-4.1 portaudio
```

Estas son bibliotecas del escritorio Linux; los motores de voz y sus modelos ya
van incluidos. No instales Python/Piper por separado.

### Opción A: instalador por usuario `.run`

1. Guarda `lector-local-0.1.0-linux-x86_64.run` en Descargas.
2. Abre una terminal en esa carpeta.
3. Da permiso de ejecución y ejecuta el instalador **sin sudo**:

   ```sh
   chmod +x lector-local-0.1.0-linux-x86_64.run
   ./lector-local-0.1.0-linux-x86_64.run
   ```

4. Espera a que termine de verificar y extraer los archivos.
5. Abre **Lector Local** desde el menú de aplicaciones. Por defecto queda instalado
   en `~/.local/share/lector-local-0.1.0`.
6. Pega un texto y prueba Kokoro/Piper desde Ajustes.
7. Continúa con la sección de tu navegador para instalar la extensión.

Para retirar esta instalación, cierra la aplicación y la extensión y ejecuta:

```sh
"${XDG_DATA_HOME:-$HOME/.local/share}/lector-local-0.1.0/lector-core" install-host --uninstall
rm -rf "${XDG_DATA_HOME:-$HOME/.local/share}/lector-local-0.1.0"
rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/applications/lector-local.desktop"
```

### Opción B: paquete `.deb`

1. Guarda `Lector Local_0.1.0_amd64.deb` en Descargas.
2. Abre una terminal en esa carpeta e instala:

   ```sh
   sudo apt install "./Lector Local_0.1.0_amd64.deb"
   ```

3. Abre **Lector Local** desde el menú de aplicaciones.
4. Prueba los motores y configura tu extensión siguiendo la sección del navegador.

Antes de desinstalar, retira los registros de navegador:

```sh
lector-core install-host --uninstall
sudo apt remove lector-local
```

### Opción C: paquete portátil `.tar.gz`

1. Extrae `lector-local-linux-x86_64.tar.gz` con el gestor de archivos.
2. Mueve la carpeta `lector-local` a una ubicación permanente. No la dejes en
   una carpeta que vayas a borrar después de la prueba.
3. Abre `lector-local-desktop`. Si el gestor de archivos no lo ejecuta, abre una
   terminal en esa carpeta y ejecuta `./lector-local-desktop`.
4. Configura el navegador desde la aplicación.

Antes de borrar o mover la carpeta, ejecuta `./lector-core install-host --uninstall`
desde ella. Si cambias su ubicación, registra otra vez los navegadores.

## macOS: entrega pendiente

No se puede enviar todavía una aplicación instalable para Mac. No hay acceso a
un Mac ni a un runner macOS autenticado para generar y verificar los binarios.
Los archivos Windows/Linux no funcionan como aplicación nativa para Mac.

Cuando exista el `.dmg` correspondiente, el procedimiento del tester será:

1. En **menú Apple → Acerca de este Mac**, identifica si tiene procesador Intel
   o chip Apple y recibe el `.dmg` de esa arquitectura.
2. Abre el `.dmg` y arrastra **Lector Local.app** a **Aplicaciones**.
3. Abre la app desde Aplicaciones. Una entrega sin firma/notarización puede ser
   bloqueada por macOS; informa del mensaje exacto si sucede.
4. Prueba Kokoro/Piper.
5. Instala la extensión y registra el navegador desde Ajustes **después** de mover
   la app a Aplicaciones.

Estos pasos son la guía prevista para una entrega futura; no confirman que haya
un `.dmg` disponible ni probado. Los requisitos definitivos se indicarán al generarlo.

## Firefox / Zen: cargar la extensión

Requiere Firefox 140 o posterior, o un Zen compatible con esa versión de Gecko.
Los pasos se repiten en cada SO, después de instalar su aplicación local.

1. Guarda `lector-extension-firefox-unsigned.xpi` en una ubicación que conserves.
2. En Firefox/Zen, escribe `about:debugging#/runtime/this-firefox` en la barra
   de direcciones y pulsa Enter.
3. Pulsa **Cargar complemento temporal** y selecciona el archivo `.xpi`.
   No lo instales desde el gestor normal de complementos: está sin firmar.
4. Abre Lector Local y entra en **Ajustes → Escucha desde tu navegador**.
5. Pulsa **Registrar Firefox**. En Windows puedes omitirlo si el registro del
   instalador ya funciona; úsalo si la extensión no conecta.
6. Recarga la extensión o pulsa **Reintentar conexión** en su popup.
7. Abre un artículo de Wikipedia y prueba la lectura de una selección y del artículo.
8. Al reiniciar Firefox/Zen, repite los pasos 2–3. No es necesario volver a registrar
   el host si la aplicación sigue en la misma ubicación.

Si recibiste `lector-extension-firefox-unsigned.zip`, también puedes descomprimirlo
y seleccionar su `manifest.json` en el paso 3. Cambiar `.zip` por `.xpi` no proporciona
firma: ambos contienen la misma extensión. La carga temporal y la necesidad de firma
para distribución permanente están descritas por
[Mozilla](https://extensionworkshop.com/documentation/develop/temporary-installation-in-firefox/)
y en su [guía de distribución](https://extensionworkshop.com/documentation/publish/signing-and-distribution-overview/).

## Chrome / Chromium / Edge / Brave / Vivaldi: cargar la extensión

1. Descomprime `lector-extension-chromium-unsigned.zip` en una carpeta permanente.
2. Abre la página de extensiones:

   | Navegador | Dirección |
   |---|---|
   | Chrome / Chromium | `chrome://extensions` |
   | Edge | `edge://extensions` |
   | Brave | `brave://extensions` |
   | Vivaldi | `vivaldi://extensions` |

3. Activa **Modo de desarrollador**.
4. Pulsa **Cargar descomprimida** y elige la carpeta que contiene `manifest.json`.
5. Copia el **ID** que aparece en la tarjeta de Lector Local; son 32 letras.
6. Abre la aplicación: **Ajustes → Escucha desde tu navegador**.
7. Pega el ID en **ID de la extensión Chromium** y pulsa
   **Registrar navegadores detectados**.
8. Recarga la extensión o pulsa **Reintentar conexión** en su popup.
9. Abre Wikipedia y prueba la lectura.

Conserva la carpeta extraída. Si reinstalas la extensión y cambia el ID, registra
el nuevo ID. Si varios navegadores muestran IDs diferentes, configura cada uno;
si el registro rechaza sustituir un ID anterior, informa del mensaje antes de
sobrescribirlo. La carga descomprimida sigue el
[procedimiento de Google](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked).

## Prueba común y cómo informar de fallos

1. Lee un texto español con Kokoro y después con Piper.
2. Pausa, reanuda y cambia la velocidad.
3. Abre un documento PDF con texto; prueba también OCR con un PDF escaneado.
4. En Wikipedia, lee una selección desde la extensión.
5. Cierra la ventana de la aplicación y comprueba que la extensión sigue pudiendo leer.
6. Repite la prueba con documentos guardados, sin conexión a Internet.
7. Si falla, envía SO y versión, arquitectura, navegador y versión, motor utilizado,
   pasos para reproducir, resultado esperado y mensaje exacto. No envíes documentos
   privados ni credenciales.

Si aparece **No such native application org.lector.local**, comprueba que la aplicación
esté instalada y que hayas registrado ese navegador en Ajustes. Para Zen usa
**Registrar Firefox**. Después pulsa **Reintentar conexión**.

La integración real del navegador se probó en Zen en Linux. Windows se comprobó
bajo Wine; falta validar su interfaz y WebView2 en Windows real. La instalación
silenciosa en Wine se probó simulando WebView2 ya presente. macOS sigue pendiente.
