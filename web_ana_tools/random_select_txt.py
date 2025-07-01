#!/usr/bin/env python3
"""
随机从 websites 目录中挑选 100 个子文件夹，并将这些文件夹中所有的 .txt 文件
复制到 web_ana_tools/outputs/random_select 目录下。

用法：
    python random_select_txt.py
"""

import os
import random
import shutil
from pathlib import Path

# 项目根目录按此脚本位置推断（即 projects/wayback_machine_downloader）
BASE_DIR = Path(__file__).resolve().parent.parent / "websites"
DEST_DIR = Path(__file__).resolve().parent / "outputs" / "random_select"
# 确保输出目录存在
DEST_DIR.mkdir(parents=True, exist_ok=True)

# 获取一级子文件夹列表
subfolders = [p for p in BASE_DIR.iterdir() if p.is_dir() and p.name != "random_select"]

if len(subfolders) < 100:
    raise ValueError(f"子文件夹不足 100 个，仅有 {len(subfolders)} 个，无法完成随机抽取。")

# 随机抽取 1000 个子文件夹
selected_folders = random.sample(subfolders, 200)

print("已随机选取以下 100 个子文件夹：")
for folder in selected_folders:
    print(" -", folder.name)

# 复制 .txt 文件
for folder in selected_folders:
    for txt_path in folder.rglob("*.txt"):
        # 目标文件名：仅使用原文件名，如存在重名则跳过
        dest_name = txt_path.name
        dest_path = DEST_DIR / dest_name

        if dest_path.exists():
            # 已存在同名文件，不进行覆盖，直接跳过
            print(f"重复文件已存在，跳过: {dest_name}")
            continue

        shutil.copy2(txt_path, dest_path)

print(f"复制完成！所有 .txt 文件已保存至: {DEST_DIR}") 