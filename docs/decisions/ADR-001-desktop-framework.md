# ADR-001: Tauri 2 y componentes React compartidos

Aceptado. Se mantiene el stack pedido por el usuario. Tauri gestiona diálogo de archivos, drag & drop y ejecución de un comando fijo del core. React renderiza documento y controles reutilizados por la extensión. La UI no importa internals Python ni recibe capacidades generales de shell.

Coste: Rust, WebKitGTK/WebView2 y empaquetar un sidecar Python en cada plataforma. Se asume para compartir tecnología de interfaz sin duplicar TTS. Los instaladores y firmas necesitan validación específica del SO.
