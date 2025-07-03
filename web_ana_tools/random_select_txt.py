#!/usr/bin/env python3
"""
随机从 websites 目录中挑选指定数量的子文件夹，并将这些文件夹中所有的 .txt 文件
复制到 web_ana_tools/outputs/random_select 目录下。

用法：
    python random_select_txt.py --random 100
"""

import os
import random
import shutil
from pathlib import Path
import argparse

# --------------------------- 主程序入口 ---------------------------

def main():
    """从 BASE_DIR 中随机抽取指定数量的子文件夹，将其中的 .txt 文件复制到 DEST_DIR"""

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="随机抽取指定数量的子文件夹并复制其中的 .txt 文件到 outputs/random_select 目录下"
    )
    parser.add_argument(
        "--random",
        "-r",
        type=int,
        default=100,
        help="要随机选择的子文件夹数量（默认 100）",
    )
    args = parser.parse_args()
    num_select = args.random

    # 项目根目录按此脚本位置推断（即 projects/wayback_machine_downloader）
    BASE_DIR = Path(__file__).resolve().parent.parent / "websites"
    DEST_DIR = Path(__file__).resolve().parent / "outputs" / "random_select"
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # 获取一级子文件夹列表
    subfolders = [p for p in BASE_DIR.iterdir() if p.is_dir() and p.name != "random_select"]

    if len(subfolders) < num_select:
        raise ValueError(
            f"子文件夹不足 {num_select} 个，仅有 {len(subfolders)} 个，无法完成随机抽取。"
        )

    # 随机抽取子文件夹
    selected_folders = random.sample(subfolders, num_select)

    print(f"已随机选取以下 {num_select} 个子文件夹：")
    for folder in selected_folders:
        print(" -", folder.name)

    # 复制 .txt 文件
    for folder in selected_folders:
        for txt_path in folder.rglob("*.txt"):
            dest_name = txt_path.name
            dest_path = DEST_DIR / dest_name

            if dest_path.exists():
                print(f"重复文件已存在，跳过: {dest_name}")
                continue

            shutil.copy2(txt_path, dest_path)

    print(f"复制完成！所有 .txt 文件已保存至: {DEST_DIR}")


if __name__ == "__main__":
    main() 