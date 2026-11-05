from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType


scriptDir = Path(__file__).resolve().parent / "script"


def getNameLower(path: Path) -> str:
    return path.name.lower()


def readTextFile(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        return f"Unable to read {path.name}: {error}"


def discoverCategories() -> list[Path]:
    if not scriptDir.exists():
        scriptDir.mkdir(parents=True)
        return []

    categories = [
        path
        for path in scriptDir.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    ]

    return sorted(categories, key=getNameLower)


def discoverAttacks(category: Path) -> list[Path]:
    attacks = [
        path
        for path in category.glob("*.py")
        if path.is_file() and not path.name.startswith("_")
    ]

    return sorted(attacks, key=getNameLower)


def loadAttack(attackPath: Path) -> ModuleType:
    moduleHash = hashlib.sha256(
        str(attackPath).encode()
    ).hexdigest()[:12]

    moduleName = f"attack_{moduleHash}"

    spec = importlib.util.spec_from_file_location(moduleName, attackPath)

    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {attackPath.name}")

    attackModule = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(attackModule)

    return attackModule


def showAttack(attackPath: Path) -> None:
    try:
        attackModule = loadAttack(attackPath)
    except Exception as error:
        print(f"\nUnable to load attack: {error}")
        input("\nPress Enter to continue...")
        return

    print(f"\n=== {attackPath.stem} ===")

    printInfo = getattr(attackModule, "printInfo", None)

    if callable(printInfo):
        try:
            info = printInfo()

            if info is not None:
                print(info)
        except Exception as error:
            print(f"Unable to display attack information: {error}")
    else:
        print("No information is available for this attack.")

    while True:
        choice = input("\n[r] Run attack  [b] Back\n> ").strip().lower()

        if choice in {"b", "back"}:
            return

        if choice in {"r", "run"}:
            start = getattr(attackModule, "start", None)

            if not callable(start):
                print("\nThis attack does not define start().")
                input("\nPress Enter to continue...")
                return

            try:
                result = start()

                if result is not None:
                    print(f"\n{result}")
            except Exception as error:
                print(f"\nAttack failed: {error}")

            input("\nPress Enter to continue...")
            return

        print("Invalid selection.")


def showCategory(category: Path) -> None:
    readmePath = category / "readme.txt"
    attacks = discoverAttacks(category)

    while True:
        print(f"\n=== {category.name} ===")

        if readmePath.exists():
            print(f"\n{readTextFile(readmePath)}")
        else:
            print("\nNo readme.txt found.")

        if not attacks:
            print("\nNo attack scripts found.")
        else:
            print("\nAttacks:")

            for index, attack in enumerate(attacks, start=1):
                print(f"{index}. {attack.stem}")

        choice = input(
            "\nSelect an attack or [b] Back: "
        ).strip().lower()

        if choice in {"b", "back"}:
            return

        try:
            attackIndex = int(choice) - 1

            if 0 <= attackIndex < len(attacks):
                showAttack(attacks[attackIndex])
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid selection.")


def main() -> None:
    print("PLC Cyber Range Attack Engine")

    while True:
        categories = discoverCategories()

        print("\n=== Categories ===")

        if not categories:
            print("No categories found.")
            print(f"Create category directories inside: {scriptDir}")
        else:
            for index, category in enumerate(categories, start=1):
                print(f"{index}. {category.name}")

        choice = input(
            "\nSelect a category, [r] Refresh, or [q] Quit: "
        ).strip().lower()

        if choice in {"q", "quit"}:
            print("Goodbye.")
            return

        if choice in {"r", "refresh"}:
            continue

        try:
            categoryIndex = int(choice) - 1

            if 0 <= categoryIndex < len(categories):
                showCategory(categories[categoryIndex])
            else:
                print("Invalid selection.")
        except ValueError:
            print("Invalid selection.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye.")

