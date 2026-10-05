"""Prepare a per-user Linux installer and browser packages from verified releases."""

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / "artifacts/releases"

HEADER = r"""#!/bin/sh
set -eu
if [ "${1:-}" = "--help" ]; then
  printf '%s\n' 'Instala Lector Local 0.1.0 para tu usuario y crea una entrada en el menú.' \
    'Linux x86_64, glibc >= 2.39, GTK3 y WebKitGTK 4.1.' \
    'No lo ejecutes con sudo. Para desinstalar, consulta GUIA-TESTERS.md.'
  exit 0
fi
if [ "$(id -u)" = 0 ]; then
  printf '%s\n' 'Ejecuta este instalador como usuario normal, sin sudo.' >&2
  exit 1
fi
if [ "$(uname -m)" != x86_64 ]; then
  printf '%s\n' 'Esta entrega requiere Linux x86_64 (Intel/AMD de 64 bits).' >&2
  exit 1
fi
for utility in awk tail sha256sum tar ldd getconf sort; do
  command -v "$utility" >/dev/null || { printf 'Falta %s\n' "$utility" >&2; exit 1; }
done
glibc_version=$(getconf GNU_LIBC_VERSION 2>/dev/null | awk '{print $2}')
if [ -z "$glibc_version" ] || [ "$(printf '%s\n' 2.39 "$glibc_version" | sort -V | head -n 1)" != 2.39 ]; then
  printf '%s\n' 'Esta entrega requiere glibc 2.39 o posterior. Consulta GUIA-TESTERS.md.' >&2
  exit 1
fi
data_root=${XDG_DATA_HOME:-"$HOME/.local/share"}
install_dir="$data_root/lector-local-0.1.0"
launcher="$data_root/applications/lector-local.desktop"
if [ -e "$install_dir" ] || [ -e "$launcher" ]; then
  printf '%s\n' 'Ya existe una instalación o una entrada en el menú. Desinstálala primero.' >&2
  exit 1
fi
mkdir -p "$data_root"
stage=$(mktemp -d "$data_root/.lector-local-install.XXXXXX")
trap 'rm -rf "$stage"' EXIT HUP INT TERM
payload_line=$(awk '/^__LECTOR_PAYLOAD_BELOW__$/ {print NR+1; exit}' "$0")
printf '%s\n' 'Verificando los archivos incluidos…'
actual=$(tail -n +"$payload_line" "$0" | sha256sum | awk '{print $1}')
if [ "$actual" != "__PAYLOAD_SHA256__" ]; then
  printf '%s\n' 'El instalador está incompleto o dañado. Descárgalo de nuevo.' >&2
  exit 1
fi
printf '%s\n' 'Extrayendo aplicación y voces…'
tail -n +"$payload_line" "$0" | tar -xz -C "$stage"
missing=$(ldd "$stage/lector-local/lector-local-desktop" | awk '/not found/ {print $1}')
if [ -n "$missing" ]; then
  printf 'Faltan bibliotecas del sistema:\n%s\nConsulta GUIA-TESTERS.md.\n' "$missing" >&2
  exit 1
fi
mv "$stage/lector-local" "$install_dir"
mkdir -p "$data_root/applications"
cat > "$launcher" <<EOF
[Desktop Entry]
Type=Application
Name=Lector Local
Comment=Lectura local de documentos con voz
Exec="$install_dir/lector-local-desktop"
Terminal=false
Categories=AudioVideo;Utility;
EOF
printf 'Instalación terminada en %s\nAbre Lector Local desde el menú de aplicaciones.\n' "$install_dir"
printf '%s\n' 'Para usar la extensión, registra el navegador desde Ajustes en la aplicación.'
exit 0
__LECTOR_PAYLOAD_BELOW__
"""


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    # Validate previous deliveries before using their content.
    for index in [RELEASES / "release.json", RELEASES / "windows/release.json"]:
        for record in json.loads(index.read_text())["files"]:
            path = index.parent / record["name"]
            if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
                raise RuntimeError(f"Entrega dañada: {path.name}")
    payload = RELEASES / "lector-local-linux-x86_64.tar.gz"
    installer = RELEASES / "lector-local-0.1.0-linux-x86_64.run"
    temporary = installer.with_suffix(".partial")
    with temporary.open("wb") as output, payload.open("rb") as source:
        output.write(HEADER.replace("__PAYLOAD_SHA256__", digest(payload)).encode("utf-8"))
        shutil.copyfileobj(source, output, 1024 * 1024)
    temporary.chmod(0o755)
    temporary.replace(installer)
    # XPI is the same ZIP container, explicitly unsigned and for temporary load.
    xpi = RELEASES / "lector-extension-firefox-unsigned.xpi"
    shutil.copy2(RELEASES / "lector-extension-firefox-unsigned.zip", xpi)
    guide = RELEASES / "GUIA-TESTERS.md"
    shutil.copy2(ROOT / "installers/GUIA-TESTERS.md", guide)
    paths = [
        installer,
        payload,
        RELEASES / "Lector Local_0.1.0_amd64.deb",
        xpi,
        RELEASES / "lector-extension-chromium-unsigned.zip",
        RELEASES / "windows/lector-local-0.1.0-windows-x64-setup.exe",
        guide,
    ]
    (RELEASES / "testers.json").write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "macos": "not built: no macOS host or authenticated CI available",
                "files": [
                    {
                        "name": p.relative_to(RELEASES).as_posix(),
                        "bytes": p.stat().st_size,
                        "sha256": digest(p),
                    }
                    for p in paths
                ],
            },
            indent=2,
        )
        + "\n"
    )
    print(installer)
    print(xpi)
    print(guide)


if __name__ == "__main__":
    main()
