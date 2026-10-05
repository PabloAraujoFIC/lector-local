# Instalador Windows desde Arch

La entrega Windows x64 se construye con Python 3.12.10 para Windows ejecutado
en Wine y con Rust MSVC mediante cargo-xwin. NSIS produce un único instalador
por usuario. El motor usa PyInstaller en modo carpeta: `lector-core.exe` y
`_internal` se instalan juntos. Así cada petición de la interfaz o extensión
evita extraer de nuevo todos los modelos. El tester solo ejecuta el instalador.

## Entorno preparado en este equipo

Todo queda en `.bootstrap/windows`, sin cambiar el Rust del sistema ni el
perfil Wine habitual:

- `wine/drive_c/Python312/python.exe`: instalador oficial de python.org.
- `requirements.txt`: exportación de `uv.lock` con `uv export --frozen
  --extra dev --no-emit-project --no-hashes` instalada con ese Python y pip.
- `rustup` y `cargo`: rustup con perfil mínimo, Rust estable y destino
  `x86_64-pc-windows-msvc`; cargo-xwin instalado con `cargo install --locked`.
- `xwin`: SDK y CRT de Microsoft descargados por cargo-xwin.
- `nsis`: paquetes `nsis` y `nsis-common` 3.10-2ubuntu2 del archivo oficial de
  Ubuntu, extraídos localmente. Ese binario compila con un directorio de stubs
  fijo; se ha adaptado la ruta `/usr/share/nsis` (cadena UTF-32LE del binario)
  a `/tmp/ll-nsis///`, manteniendo su longitud. `/tmp/ll-nsis` enlaza a
  `.bootstrap/windows/nsis/usr/share/nsis`. `NSISDIR` apunta al mismo directorio.
- `vcredist/runtime`: DLL x64 oficiales de Visual C++ 14.44.35211 obtenidas de
  `https://aka.ms/vs/17/release/vc_redist.x64.exe`. Se extraen los contenedores CAB
  del bootstrapper y el CAB x64 del runtime; se preserva la licencia de Microsoft.
  Se incluyen DLL reales, ya que PyInstaller descarta las implementaciones de Wine.
- WebView2: Tauri descarga el instalador offline oficial de Microsoft durante
  la compilación y lo incorpora en NSIS.

Si `/tmp` se ha limpiado, recrea el enlace antes de compilar:

```sh
ln -s "$PWD/.bootstrap/windows/nsis/usr/share/nsis" /tmp/ll-nsis
```

## Repetir la compilación

Desde la raíz del proyecto:

```sh
.venv/bin/python scripts/build_windows_wine.py
```

Necesita acceso de red durante el build y permiso para los sockets locales de
Wine. `--reuse-core` permite reutilizar un motor ya generado; se ejecuta de nuevo
su prueba offline antes de incorporarlo. Las salidas Windows y las dos extensiones
están en `artifacts/releases/windows/`. El índice contiene tamaños y SHA-256 y
conserva por separado los paquetes Linux anteriores.

## Validación

El motor empaquetado se prueba en almacenamiento vacío, con conexiones externas
bloqueadas: síntesis española Kokoro/Piper y OCR de un PDF escaneado. Además se
comprueba la comunicación Native Messaging y el servicio compartido bajo Wine.
La integridad de NSIS y su contenido se comprueban antes de entregar.

La entrega 0.1.0 ha pasado las pruebas de audio/Native Messaging para ambos
motores, 47 pruebas Python en Linux (una opcional omitida) y ocho de IPC/recursos
con Python Windows bajo Wine. En un segundo prefijo sin Python instalado se ha
comprobado la instalación silenciosa, el self-test del motor instalado con DLL
Microsoft incluidas, el registro Firefox en HKCU y la retirada al desinstalar.
Para esa prueba se simula WebView2 presente mediante una clave del registro del
prefijo aislado; no se presenta como una prueba de instalación de WebView2 ni de
la interfaz. Resultados y SHA-256: `artifacts/releases/windows/release.json`.

Estas pruebas no sustituyen instalar la aplicación, abrir su interfaz WebView2
y usar navegadores en Windows real. El instalador y las extensiones se entregan
sin firma de editor. Instrucciones del tester: `installers/windows/LEEME.txt`.

Referencias: [compilación Windows de Tauri](https://tauri.app/distribute/windows-installer/),
[PyInstaller](https://pyinstaller.org/en/stable/usage.html),
[redistribución de Visual C++](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files).
