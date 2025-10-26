import os
from pathlib import Path

# Имя этого скрипта и файлов/папок, которые нужно исключить
EXCLUDE_NAMES = {
    ".env",
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "project_combined.txt",
}
SCRIPT_NAME = Path(__file__).name

def should_exclude(path: Path) -> bool:
    """Проверяет, нужно ли пропустить путь."""
    return any(part in EXCLUDE_NAMES for part in path.parts) or path.name == SCRIPT_NAME

def main():
    project_root = Path(".")
    output_file = project_root / "project_combined.txt"

    with open(output_file, "w", encoding="utf-8") as out_f:
        # Собираем все .py файлы
        py_files = sorted(project_root.rglob("*.py"))

        for file_path in py_files:
            if should_exclude(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                content = f"<<< ОШИБКА ЧТЕНИЯ ФАЙЛА: {e} >>>"

            # Путь относительно корня проекта
            rel_path = file_path.relative_to(project_root).as_posix()
            out_f.write(f"--{rel_path}--\n")
            out_f.write(content)
            out_f.write("\n\n")

    print(f"✅ Проект объединён в файл: {output_file.absolute()}")

if __name__ == "__main__":
    main()