; Per-user NSIS installer. Never register into an elevated user's profile.
!macro NSIS_HOOK_POSTINSTALL
  nsExec::ExecToLog '"$INSTDIR\core\lector-core.exe" install-host --channel production'
  Pop $0
  ${If} $0 != 0
    DetailPrint "Registro Firefox pendiente: usa Ajustes > Navegadores en Lector Local."
  ${EndIf}
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  nsExec::ExecToLog '"$INSTDIR\core\lector-core.exe" install-host --uninstall'
  Pop $0
  ${If} $0 != 0
    DetailPrint "No se pudieron retirar los registros del host."
  ${EndIf}
!macroend
