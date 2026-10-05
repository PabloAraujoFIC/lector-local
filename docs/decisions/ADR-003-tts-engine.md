# ADR-003: Kokoro-82M ONNX como primer motor

Aceptado para MVP, pendiente comparación perceptiva. Kokoro-82M tiene modelo Apache-2.0, voces españolas y ejecución CPU. Se utiliza kokoro-onnx (MIT) para evitar instalar PyTorch y su ecosistema GPU como requisito básico. Archivos locales fijados a release v1.0, 354 MB, con SHA-256. El runtime no descarga pesos ni voces.

TTSEngine separa motor de protocolo/UI; un adaptador Piper opcional está preparado. Piper actual GPL-3.0 y sus voces tienen licencias propias. No se asume que todas las voces son aptas para cualquier distribución.

CPU funciona. Auto/CUDA utilizan proveedor disponible con fallback. MPS no está implementado en ONNX: se rechaza y se muestra como no disponible. Idioma auto toma el idioma de voz; detección textual local queda pendiente. No se declara alemán compatible mediante una voz española.

Una síntesis española real valida funcionalidad técnica; no demuestra comodidad durante horas ni superioridad frente a Piper. La elección definitiva requiere prueba de escucha de Dora/Alex/Santa y modelos alternativos.

Fuentes: [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), [voces](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md), [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), [Piper](https://github.com/OHF-Voice/piper1-gpl).
