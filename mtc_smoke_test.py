import sys
import types
import importlib.util
from pathlib import Path
from typing import List

from adbutils import adb


ROOT = Path(__file__).resolve().parent


def _ensure_mtc_package() -> None:
    if "mtc" not in sys.modules:
        mtc_pkg = types.ModuleType("mtc")
        mtc_pkg.__path__ = []  # type: ignore[attr-defined]
        sys.modules["mtc"] = mtc_pkg


def _load_submodule(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def setup_mtc_modules() -> None:
    """Dynamically load mtc.* modules from workspace for testing."""
    _ensure_mtc_package()
    _load_submodule("mtc.touch", ROOT / "mtc-base" / "src" / "mtc" / "touch.py")
    _load_submodule("mtc.utils", ROOT / "mtc-utils" / "src" / "mtc" / "utils.py")
    _load_submodule("mtc.adb", ROOT / "mtc-adb" / "src" / "mtc" / "adb.py")
    _load_submodule(
        "mtc.minitouch",
        ROOT / "mtc-minitouch" / "src" / "mtc" / "minitouch.py",
    )
    _load_submodule(
        "mtc.maatouch",
        ROOT / "mtc-maatouch" / "src" / "mtc" / "maatouch.py",
    )
    _load_submodule("mtc.mumu", ROOT / "mtc-mumu" / "src" / "mtc" / "mumu.py")


def _get_first_device_serial() -> str | None:
    devices: List = adb.device_list()
    print(f"ADB devices detected: {[d.serial for d in devices]}")
    if not devices:
        return None
    return devices[0].serial


def test_adb_touch() -> None:
    from mtc.adb import ADBTouch  # type: ignore[import]

    print("\n== Testing ADBTouch ==")
    serial = _get_first_device_serial()
    if not serial:
        print("SKIP: no adb devices available")
        return

    print(f"Using device: {serial}")
    try:
        touch = ADBTouch(serial)
        touch.click(100, 100, 100)
        touch.swipe([(100, 100), (300, 300)], 500)
    except Exception as exc:  # pragma: no cover - smoke output
        print(f"ADBTouch FAILED: {exc}")
        return

    print("ADBTouch OK")


def test_minitouch() -> None:
    from mtc.minitouch import MiniTouch  # type: ignore[import]

    print("\n== Testing MiniTouch ==")
    serial = _get_first_device_serial()
    if not serial:
        print("SKIP: no adb devices available")
        return

    print(f"Using device: {serial}")
    touch: MiniTouch | None = None
    try:
        touch = MiniTouch(serial)
    except Exception as exc:  # pragma: no cover - smoke output
        print(f"MiniTouch init FAILED: {exc}")
        return

    try:
        touch.click(100, 100, 100)
        touch.swipe([(100, 100), (200, 200), (300, 300)], 500)
        print("MiniTouch OK")
    except Exception as exc:  # pragma: no cover - smoke output
        print(f"MiniTouch FAILED during operations: {exc}")
    finally:
        if touch is not None:
            try:
                touch.stop()
            except Exception:
                pass


def test_maatouch() -> None:
    from mtc.maatouch import MaaTouch  # type: ignore[import]

    print("\n== Testing MaaTouch ==")
    serial = _get_first_device_serial()
    if not serial:
        print("SKIP: no adb devices available")
        return

    print(f"Using device: {serial}")
    touch: MaaTouch | None = None
    try:
        touch = MaaTouch(serial)
    except Exception as exc:  # pragma: no cover - smoke output
        print(f"MaaTouch init FAILED: {exc}")
        return

    try:
        touch.click(100, 100, 100)
        touch.swipe([(100, 100), (200, 200), (300, 300)], 500)
        print("MaaTouch OK")
    except Exception as exc:  # pragma: no cover - smoke output
        print(f"MaaTouch FAILED during operations: {exc}")


def test_mumu() -> None:
    from mtc.mumu import MuMuTouch  # type: ignore[import]

    print("\n== Testing MuMuTouch ==")
    try:
        touch = MuMuTouch(0)
    except Exception as exc:  # pragma: no cover - smoke output
        print(f"MuMuTouch init FAILED (likely no MuMu installed): {exc}")
        return

    try:
        touch.click(100, 100, 100)
        touch.swipe([(100, 100), (200, 200), (300, 300)], 500)
        print("MuMuTouch OK")
    except Exception as exc:  # pragma: no cover - smoke output
        print(f"MuMuTouch FAILED during operations: {exc}")


def main() -> None:
    setup_mtc_modules()
    test_adb_touch()
    test_minitouch()
    test_maatouch()
    test_mumu()


if __name__ == "__main__":
    main()

