# Validación de la entrega 0.2.1

La corrección de audio Linux está incluida en esta versión. Las bibliotecas ALSA, JACK y PortAudio se resuelven desde el sistema instalado; el runtime selecciona el dispositivo virtual PipeWire/PulseAudio cuando está disponible. El usuario ha confirmado el funcionamiento de los altavoces del portátil en Arch.

Los cuatro instaladores se han construido y comprobado en runners nativos: Windows 2022 x64, Ubuntu 22.04 x64, macOS Intel y macOS Apple Silicon. El [workflow de esta entrega](https://github.com/PabloAraujoFIC/lector-local/actions/runs/37384700185) conserva sus resultados. Las extensiones y las fuentes AMO son idénticas byte por byte entre plataformas.

Validación local: 53 pruebas Python, cuatro pruebas web, Ruff/MyPy, TypeScript/ESLint y comprobación de versiones. Mozilla no reporta errores; los cuatro avisos DOM de React/Readability siguen documentados. El ZIP AMO reconstruye exactamente cada archivo del bundle Firefox.

El TAR Ubuntu distribuible se ha extraído y probado en este Arch en un perfil aislado: Piper y Kokoro terminan la reproducción sin errores y hay señal en el monitor de la salida analógica. El self-test con red bloqueada sintetiza ambos motores y verifica OCR. El DEB declara libasound2, libportaudio2, libwebkit2gtk-4.1-0 y libgtk-3-0; el TAR no contiene libasound/libjack/libportaudio del host de build.

Los certificados Windows/Apple, la notarización y la firma AMO siguen pendientes: SIGNING_REQUIRED. CI no acredita la prueba manual de instalación/interfaz/audio en Windows/macOS. La guía, los tamaños y las sumas exactas se descargan desde la [Release 0.2.1](https://github.com/PabloAraujoFIC/lector-local/releases/tag/v0.2.1).
