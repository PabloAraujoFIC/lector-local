"""Build the native executable on the current OS. No cross-compilation assumption."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="Rust target triple; defaults to rustc host")
    parser.add_argument("--output-dir", type=Path, help="Separate build artifacts directory")
    parser.add_argument("--windows-runtime", type=Path, help="Official Visual C++ runtime DLLs")
    parser.add_argument("--signed", action="store_true")
    args = parser.parse_args()
    if args.signed and sys.platform not in {"win32", "darwin"}:
        parser.error("La firma nativa requiere Windows o macOS")
    signing = []
    if args.signed and sys.platform == "darwin":
        identity = os.environ.get("APPLE_SIGNING_IDENTITY")
        if not identity or identity == "-":
            parser.error("Falta APPLE_SIGNING_IDENTITY de Developer ID")
        signing = [
            "--codesign-identity",
            identity,
            "--osx-entitlements-file",
            str(
                Path(__file__).resolve().parents[1]
                / "apps/desktop/src-tauri/macos/entitlements.plist"
            ),
        ]
    root = Path(__file__).resolve().parent.parent
    output = (
        args.output_dir.resolve()
        if args.output_dir
        else root / ("artifacts/windows" if sys.platform == "win32" else "artifacts")
    )
    from prepare_assets import prepare

    assets = prepare(root)
    # A Windows Python runtime (including Wine) packages Windows wheels and the
    # Windows bootloader. Rust itself can run separately on the Linux host.
    if sys.platform == "win32":
        native_target = "x86_64-pc-windows-msvc" if sys.maxsize > 2**32 else "i686-pc-windows-msvc"
    else:
        native_target = next(
            line.split(": ", 1)[1]
            for line in subprocess.check_output(["rustc", "-vV"], text=True).splitlines()
            if line.startswith("host:")
        )
    if args.target and args.target != native_target:
        parser.error("PyInstaller requiere construir el core en el SO y arquitectura de destino")
    runtime_args = []
    if args.windows_runtime:
        if sys.platform != "win32":
            parser.error("--windows-runtime requiere un intérprete Python de Windows")
        for name in ["msvcp140.dll", "msvcp140_1.dll", "vcruntime140.dll", "vcruntime140_1.dll"]:
            if not (args.windows_runtime / name).is_file():
                parser.error(f"Falta una biblioteca de Microsoft: {name}")
        for item in sorted(args.windows_runtime.glob("*.dll")):
            runtime_args += ["--add-binary", str(item.resolve()) + os.pathsep + "."]
        license_file = args.windows_runtime / "Microsoft-Visual-C++-License.rtf"
        if not license_file.is_file():
            parser.error("Falta la licencia del runtime redistribuible de Microsoft")
        runtime_args += [
            "--add-data",
            str(license_file.resolve()) + os.pathsep + "bundled-assets/licenses",
        ]
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            *signing,
            "--onedir",
            *runtime_args,
            "--exclude-module",
            "piper.train",
            "--exclude-module",
            "onnxruntime.transformers",
            "--exclude-module",
            "onnxruntime.quantization",
            "--add-data",
            str(root / "core/reader_core/distribution.json") + os.pathsep + "reader_core",
            "--add-data",
            str(root / "core/reader_core/model_catalog.json") + os.pathsep + "reader_core",
            "--name",
            "lector-core",
            "--paths",
            str(root / "core"),
            "--collect-all",
            "kokoro_onnx",
            "--collect-all",
            "piper",
            "--recursive-copy-metadata",
            "piper-tts",
            "--add-data",
            str(assets) + os.pathsep + "bundled-assets",
            "--collect-all",
            "espeakng_loader",
            "--collect-all",
            "language_tags",
            "--collect-all",
            "segments",
            "--collect-all",
            "csvw",
            "--collect-all",
            "phonemizer",
            "--copy-metadata",
            "phonemizer-fork",
            "--collect-all",
            "onnxruntime",
            "--hidden-import",
            "sounddevice",
            "--collect-all",
            "soundfile",
            "--hidden-import",
            "striprtf.striprtf",
            "--hidden-import",
            "pymupdf",
            "--distpath",
            str(output / "core"),
            "--workpath",
            str(output / "pyinstaller"),
            "--specpath",
            str(output),
            str(root / "native-host/entrypoint.py"),
        ],
        check=True,
    )
    import shutil

    suffix = ".exe" if sys.platform == "win32" else ""
    executable = output / "core/lector-core" / ("lector-core" + suffix)
    subprocess.run([str(executable), "self-test"], check=True)
    if args.signed and sys.platform == "win32":
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts/sign_windows.py"),
                str(executable),
            ],
            check=True,
        )
    destination = root / (
        "apps/desktop/src-tauri/runtime-windows"
        if sys.platform == "win32"
        else "apps/desktop/src-tauri/runtime"
    )
    shutil.rmtree(destination, ignore_errors=True)
    shutil.copytree(executable.parent, destination)
    print(destination)


if __name__ == "__main__":
    main()
