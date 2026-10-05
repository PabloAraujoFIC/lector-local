# Protocolo v1

Todos los clientes envían objetos JSON, nunca código, objetos Python serializados ni comandos de shell.

```json
{"protocol_version":1,"id":"uuid","type":"command","command":"speak_text","payload":{"text":"Hola mundo.","title":"Selección"}}
```

```json
{"protocol_version":1,"id":"uuid","type":"response","success":true,"payload":{"status":"playing"}}
```

```json
{"protocol_version":1,"id":"uuid","type":"response","success":false,"error":{"code":"model_missing","message":"Instala el modelo local."}}
```

```json
{"protocol_version":1,"type":"event","event":"state","payload":{"status":"paused","chunk":3,"progress":0.37}}
```

Los ejemplos de estado son abreviados; la respuesta real incluye `settings`, `document` (resumen), `paragraph_id`, offsets, segundos, revisión y eventos. `document_page` devuelve párrafos separados. `id` es una cadena de 1 a 100 caracteres. Los campos extra se rechazan. Versión distinta devuelve `protocol_mismatch`.

| Comando | Payload | Acceso |
|---|---|---|
| state | `{}` | Ambos |
| models | `{}` | Ambos |
| load_document | `{path}` | Solo escritorio |
| speak_text | `{text,title?,start_paragraph?}` | Ambos |
| document_page | `{start?,count?}`; máximo 150 párrafos | Ambos |
| play / resume / pause / stop | `{}` | Ambos |
| next / previous | `{}`; párrafo siguiente/anterior | Ambos |
| seek | Uno de `{chunk}`, `{paragraph}`, `{seconds}`; segundos relativos | Ambos |
| settings | `{values:{speed,voice,language,...}}` | Ambos |
| clear_cache | `{}` | Ambos |

Voz, idioma y motor se validan conjuntamente; actualiza esos campos en el mismo mensaje. Velocidad 0.5–2.0, volumen 0–1, buffer 1–6, caché 32–4096 MB. No existe un comando de descarga del modelo accesible al contenido web. La descarga solo se inicia mediante el comando fijo de Tauri o CLI explícita.

Framing Native Messaging: entero uint32 nativo little-endian de longitud de bytes UTF-8 seguido del JSON. Límite conservador 900.000 bytes en ambos sentidos, por debajo del máximo host→browser de Chromium. EOF/truncamiento/tamaño inválido cierra el canal. Las respuestas mantienen ID; los eventos no consumen IDs pendientes.

IPC entre bridges y daemon utiliza el mismo framing y un envelope `{token,origin,request}`. El token nunca se envía a la extensión ni se registra. Los mensajes de origen `browser` no pueden cargar rutas. No se utiliza HTTP ni CORS.
