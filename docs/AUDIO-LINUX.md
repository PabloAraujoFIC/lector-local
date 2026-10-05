# Salida de audio en Linux

Lector Local usa PipeWire o PulseAudio a través de ALSA cuando hay un dispositivo de sesión disponible. La salida física la gestiona el sistema: altavoces, auriculares por cable, HDMI o Bluetooth. La aplicación no fija un índice de tarjeta física. En sistemas sin estos dispositivos virtuales se conserva la salida predeterminada de PortAudio.

El runtime Linux utiliza las bibliotecas ALSA, JACK y PortAudio de la distribución instalada. No se deben copiar las del host de construcción: ALSA busca complementos en rutas específicas de cada distribución. Las bibliotecas Ubuntu empaquetadas en 0.2.0 impedían encontrar PipeWire en Arch y PortAudio seleccionaba hw:0,0. Esa tarjeta rechazaba los 22050 Hz de Piper y los 24000 Hz de Kokoro con PaErrorCode -9997. Bluetooth no presentaba el mismo fallo.

Los nuevos paquetes DEB declaran libasound2 y libportaudio2. Para el tar en Arch hacen falta alsa-lib, portaudio y el puente pipewire-alsa, además de GTK/WebKit. Python y los motores TTS siguen incluidos.

## Reparación comprobada en el equipo local · 2026-10-06

Se retiró la preferencia HDMI de WirePlumber que apuntaba a una salida NVIDIA inactiva mediante wpctl clear-default 0. La salida disponible es Audio Interno Estéreo analógico, puerto Altavoces, sin mute. Se mantuvieron las preferencias Bluetooth.

Se sustituyó el core instalado por un build local corregido, conservando core-before-audio-fix junto al core nuevo y las bibliotecas anteriores en artifacts/validation/audio-arch-backup. Este build local utiliza bibliotecas de Arch y no se ofrece como paquete Ubuntu genérico. La Release 0.2.0 publicada previamente no se ha sustituido; la corrección se aplicará a los siguientes builds.

La prueba del runtime instalado reproduce texto real con Kokoro y Piper, termina sin errores y captura una señal no nula en el monitor de la salida analógica. El informe está en artifacts/validation/audio-arch-fixed.json. Las pruebas no permiten confirmar físicamente la audición, ni simulan la inserción de un conector de auriculares. Esas comprobaciones requieren al usuario frente al equipo.
