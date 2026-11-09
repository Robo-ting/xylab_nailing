"""只读校验迁移后的核心文件。仅依赖 Python 标准库，不改写任何被校验文件。"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path, help="迁移后的论文根目录，例如 E:\\论文")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("文件校验清单.json"))
    parser.add_argument("--include-optional", action="store_true", help="同时校验历史预览、上传图片和训练证据")
    args = parser.parse_args()
    root = args.project_root.resolve()
    if not root.is_dir():
        parser.error(f"项目根目录不存在：{root}")
    data = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
    good = missing = changed = skipped = 0
    for item in data["files"]:
        if not item["required"] and not args.include_optional:
            skipped += 1
            continue
        path = (root / item["path"]).resolve()
        if not path.is_relative_to(root):
            print(f"非法清单路径：{item['path']}")
            return 2
        if not path.is_file():
            print(f"缺失：{item['path']}")
            missing += 1
        elif path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
            print(f"内容变化：{item['path']}")
            changed += 1
        else:
            good += 1
    print(f"一致 {good}；缺失 {missing}；内容变化 {changed}；未校验可选文件 {skipped}。")
    print("此结果只证明清单内文件是否与交接快照一致，不代表软件运行、模型权重完整或软著申请通过。")
    return 1 if missing or changed else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
