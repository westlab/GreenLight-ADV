import json
import os

# 許可するテキスト系ファイルの拡張子
ALLOWED_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".csv",
    ".html",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".c",
    ".xml",
    ".yml",
    ".yaml",
    ".ini",
    ".cfg",
    ".sh",
    ".bat",
}


def is_text_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def read_file_content(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        return None  # バイナリファイルや文字化けは除外
    except Exception as e:
        print(f"[読み取り失敗] {filepath}: {e}")
        return None


def collect_text_files_info(root_dir):
    data = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            if is_text_file(full_path):
                content = read_file_content(full_path)
                if content is not None:
                    file_info = {
                        "title": fname,
                        "content": content,
                        "file_type": os.path.splitext(fname)[1].lstrip("."),
                    }
                    data.append(file_info)
    return data


def main():
    root_folder = os.getcwd()  # ← カレントディレクトリを自動設定
    output_file = "text_files_summary.json"
    result = collect_text_files_info(root_folder)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"{len(result)} 件のテキストファイルを {output_file} に保存しました。")


if __name__ == "__main__":
    main()
