# Recursos incluidos

Los instaladores incluyen Python, los dos motores y sus bibliotecas, modelos y
fonemizadores. Las descargas ocurren durante la compilación; cada recurso se
verifica mediante tamaño y SHA-256. La lectura no necesita conexión ni paquetes
instalados por el usuario. Los modelos importados completos tienen prioridad.

- Kokoro-82M v1.0 y voces: https://huggingface.co/hexgrad/Kokoro-82M,
  Apache-2.0; texto de licencia en `licenses/Kokoro-Apache-2.0.txt`.
- Piper: https://github.com/OHF-Voice/piper1-gpl, GPL-3.0;
  texto en `licenses/Piper-GPL-3.0.txt`. La distribución incluye los metadatos
  y avisos del paquete y eSpeak. Código fuente del motor: el tag v1.8.0 del
  repositorio anterior; las versiones exactas están en `uv.lock`.
- Voz Piper española: `es_ES-sharvard-medium`, sin modificar salvo renombrar
  sus archivos como `piper_es.onnx` y `piper_es.onnx.json`.
  Fuente: https://huggingface.co/rhasspy/piper-voices/tree/c10ece1aade47bb51c153c893d14e5bf8e5b7117/es/es_ES/sharvard/medium.
  Se conserva su `MODEL_CARD`. El corpus Spanish Harvard procede de
  https://datashare.ed.ac.uk/handle/10283/574, distribuido bajo CC BY 3.0
  (https://creativecommons.org/licenses/by/3.0/), según la ficha de la voz.
- OCR: Tesseract integrado en PyMuPDF y datos `tessdata_fast` 4.1.0 para
  español, inglés, francés, alemán, italiano y portugués, Apache-2.0.
  Fuente: https://github.com/tesseract-ocr/tessdata_fast/tree/4.1.0;
  licencia en `licenses/Tesseract-Apache-2.0.txt`.

La aplicación utiliza CPU por defecto y automáticamente. CUDA solo acelera
la lectura si el equipo ya dispone de un proveedor compatible; no es necesaria.
Windows incluye el instalador offline de WebView2. En Linux la interfaz Tauri
utiliza GTK/WebKitGTK del sistema: el DEB declara estos requisitos y el TAR
portátil requiere que estén presentes. Un TAR Tauri no es una distribución
Linux independiente de las bibliotecas del sistema.

Para redistribuir, acompañar los binarios con el código de esta aplicación y
las fuentes correspondientes de sus dependencias copyleft. Esta nota y los
metadatos empaquetados no sustituyen una entrega completa de dichas fuentes.
