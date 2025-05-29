import pandas as pd
import subprocess
import os
from datetime import datetime


def clean_url(url):
    url = url.strip()           # 去除首尾空格
    url = url.lower()           # 全部转小写
    url = url.replace('http://', '').replace('https://', '')  # 移除协议头
    return url

def read_urls_from_excel(file_path, base_dir="websites"):
    try:
        df = pd.read_excel(file_path)
        urls = [clean_url(url) for url in df.iloc[:, 0].dropna().tolist()]
        urls = list(set(urls))  # 去重

        # 获取已下载的目录名
        existing_dirs = set(os.listdir(base_dir)) if os.path.exists(base_dir) else set()

        # 过滤出未处理的URL
        pending_urls = [url for url in urls if url not in existing_dirs]

        # 输出为 Excel 文件
        if pending_urls:
            output_df = pd.DataFrame(pending_urls, columns=["Pending URLs"])
            output_df.to_excel("domains_remain_remain.xlsx", index=False)
            print(f"✅ 未处理的 URL 已保存至 domains_2_remain.xlsx")
        else:
            print("🎉 所有 URL 都已处理，无需输出文件。")

        return pending_urls, len(urls), len(pending_urls)
    except Exception as e:
        print(f"❌ 读取Excel文件出错: {e}")
        return [], 0, 0

def download_wayback_snapshots(urls):
    base_dir = "websites"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    failed_logs = [] #记录每次请求失败的原因、方便后续排查

    for url in urls:
        folder_name = os.path.join(base_dir, url)
        if os.path.isdir(folder_name):
            print(f"⏩ 已存在目录，跳过: {url}")
            continue

        full_url = f"https://{url}"
        command = f'ruby bin/wayback_machine_downloader {full_url} -sl -f 2009 --concurrency 15'
        print(f"⚡ 开始下载: {full_url}")
        try:
            subprocess.run(command, shell=True, check=True)
            print(f"✅ 下载完成: {full_url}")
        except subprocess.CalledProcessError as e:
            error_msg = str(e)
            print(f"⚠️ 下载失败: {full_url}，错误信息: {error_msg}")
            failed_logs.append({
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "URL": url, 
                "Error": error_msg
                })
    
    # 保存失败日志
    if failed_logs:
        df_failed = pd.DataFrame(failed_logs)
        df_failed.to_csv("failed_urls.csv", mode='a', header=not os.path.exists("failed_urls.csv"), index=False, encoding='utf-8-sig')
        print(f"🚨 共 {len(failed_logs)} 个URL下载失败，已记录到 failed_urls.csv")
    

if __name__ == "__main__":
    file_name = "domains_remain.xlsx"
    urls, total_count, pending_count = read_urls_from_excel(file_name)
    if urls:
        print(f"📊 总URL数: {total_count}，已处理: {total_count - pending_count}，待处理: {pending_count}")
        download_wayback_snapshots(urls)
    else:
        print("🚨 没有需要处理的URL，脚本结束。")