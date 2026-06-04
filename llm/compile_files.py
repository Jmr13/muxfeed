import os

SOURCE_DIR = "./"
OUTPUT_FILE_PREFIX = "compiled_python"
MAX_FILE_SIZE = 12 * 1024 * 1024

IGNORE_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".pytest_cache", "tests", "docs", "llm", "./",}
IGNORE_FILES = {".DS_Store", "conftest.py", "compile.py"}

def get_python_files(directory):
    py_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file in IGNORE_FILES or not file.endswith(".py"):
                continue
            py_files.append(os.path.join(root, file))
    return py_files


def compile_to_md(files, output_prefix, max_size):
    file_count = 1
    current_size = 0
    current_file = open(f"{output_prefix}_{file_count}.md", "w", encoding="utf-8")

    for file_path in files:
        header = f"## {file_path}\n\n"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        code_block = f"```python\n{content}\n```\n\n"

        chunk = header + code_block
        chunk_size = len(chunk.encode("utf-8"))

        if current_size + chunk_size > max_size:
            current_file.close()
            file_count += 1
            current_file = open(f"{output_prefix}_{file_count}.md", "w", encoding="utf-8")
            current_size = 0

        current_file.write(chunk)
        current_size += chunk_size

    current_file.close()
    print(f"Compiled {len(files)} Python files into {file_count} Markdown file(s).")

if __name__ == "__main__":
    python_files = get_python_files(SOURCE_DIR)
    compile_to_md(python_files, OUTPUT_FILE_PREFIX, MAX_FILE_SIZE)