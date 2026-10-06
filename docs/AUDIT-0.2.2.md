# Validación de la entrega 0.2.2

Cuando el navegador comunica que no existe org.lector.local, el popup muestra «Necesitas instalar Lector Local», «Descargar aplicación», un enlace a los instaladores e instrucciones de GitHub y «Ya la instalé — reintentar». El enlace apunta a la Release de la versión declarada por la extensión. Los controles de lectura se ocultan mientras se muestra este aviso. El botón de reintento conecta y retira el aviso cuando el programa responde; otros errores conservan el flujo de conexión habitual.

Se ha probado en Zen y Chromium reales con perfiles y registros aislados. Ambos muestran el aviso con el host ausente y conectan tras registrar el programa sin reiniciar el navegador. Chromium verifica que el botón abre la URL correcta en otra pestaña; la respuesta de esa URL se simula únicamente en la prueba para evitar navegar a una Release todavía en borrador. Zen comprueba ambas URLs. También se verifican mensajes nativos, preferencias y ausencia de errores del popup.

Pasan 53 pruebas Python, cuatro pruebas web y los controles Ruff/MyPy, TypeScript/ESLint, versiones y empaquetado. Mozilla no reporta errores; permanecen los cuatro avisos DOM documentados de React/Readability. Las fuentes AMO reconstruyen cada archivo del bundle byte por byte.

Los instaladores Windows, Linux y macOS Intel/Apple Silicon y su publicador han pasado en runners nativos: [workflow 0.2.2](https://github.com/PabloAraujoFIC/lector-local/actions/runs/37426254190). Los ZIP de extensión son idénticos entre plataformas. Los archivos, tamaños, sumas y guía se publican en la [Release 0.2.2](https://github.com/PabloAraujoFIC/lector-local/releases/tag/v0.2.2).

El repositorio es público. Las firmas oficiales Windows/Apple, notarización y firma AMO siguen pendientes: SIGNING_REQUIRED. CI no sustituye las pruebas manuales de instalación/interfaz/audio de Windows y macOS.
