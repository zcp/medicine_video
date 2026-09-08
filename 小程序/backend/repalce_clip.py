import os
import re
import requests
import pandas as pd
from urllib.parse import urlparse

# ===== 需要你根据实际情况修改的配置 =====
EXCEL_PATH = "1125下午六点回放链接.xlsx"      # 原始 Excel 路径
OUTPUT_EXCEL_PATH = "1130下午10点回放链接_带mp2链接.xlsx"  # 结果 Excel 路径

M3U8_URL_COLUMN = "剪辑回放链接"                 # Excel 中存放 m3u8 地址的列名
NEW_URL_COLUMN = "mp2回放链接"                  # 新列名，写入 mp2 域名下的新 m3u8 URL

DOWNLOAD_DIR = "clip"                 # 本地保存 m3u8 的目录（要和 nginx 的 alias 对应）
BASE_URL = "https://mp2.dayilive.com/clip"     # 你的新域名前缀
# =====================================


def ensure_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def extract_new_filename_from_url(url: str) -> str:
    """
    从原始 m3u8 URL 中提取最后 10 位字母/数字作为新文件名（再加 .m3u8）
    例如：
      https://.../32c47d60180f4f2bbe5e04e0b4307431.m3u8
      -> 取 basename: 32c47d60180f4f2bbe5e04e0b4307431
      -> 最后 10 位: 0b4307431 之类（视具体字符串而定）
    """
    parsed = urlparse(url)
    basename = os.path.basename(parsed.path)          # xxx.m3u8
    name_without_ext, ext = os.path.splitext(basename)

    # 只保留字母数字
    alnums = re.findall(r"[0-9A-Za-z]", name_without_ext)
    if not alnums:
        raise ValueError(f"无法从文件名中提取字母数字: {basename}")

    last10 = "".join(alnums[-10:])  # 长度不足 10 就全要
    new_filename = f"{last10}.m3u8"
    return new_filename


def download_m3u8(url: str, save_path: str, timeout: int = 15):
    """
    下载 m3u8 文本文件并保存到 save_path
    """
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()  # 非 200 会抛异常
    # 以文本方式保存（一般是 UTF-8 或 ASCII）
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(resp.text)


import os
from pathlib import Path

def process_m3u8_files_in_folder(folder_path_str: str):
    """
    遍历指定文件夹中的所有 .m3u8 文件，
    并将其中 http:// 开头的 .ts 链接替换为 https://。

    此函数会保持所有其他行（包括注释、标签和
    已经是 https 的链接）原封不动。

    参数:
    folder_path_str (str): 包含 .m3u8 文件的文件夹路径，例如 'clip'。
    """

    # 将字符串路径转换为更易于操作的 Path 对象
    folder_path = Path(folder_path_str)

    # 检查文件夹是否存在
    if not folder_path.is_dir():
        print(f"❌ 错误：找不到文件夹 '{folder_path_str}'。")
        print("请确保脚本与 'clip' 文件夹在同一目录下，或者提供了正确的路径。")
        return

    print(f"--- 🚀 开始处理文件夹: {folder_path.resolve()} ---")

    # 使用 .glob('*.m3u8') 查找所有 m3u8 文件
    m3u8_files = list(folder_path.glob('*.m3u8'))

    if not m3u8_files:
        print(f"⚠️ 警告：在 '{folder_path_str}' 中没有找到 .m3u8 文件。")
        return

    total_files_changed = 0
    total_links_changed = 0

    # 遍历找到的每个 m3u8 文件
    for file_path in m3u8_files:
        print(f"\n📄 正在分析文件: {file_path.name}")

        try:
            # --- 1. 读取文件所有行 ---
            # 我们保留原始行（包含换行符），以确保精确写回
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            new_lines = []
            file_links_changed = 0

            # --- 2. 逐行检查和替换 ---
            for line in lines:
                # 去除行首尾的空白符（如换行符）仅用于判断
                stripped_line = line.strip()

                # 核心逻辑：
                # 1. 是否以 'http://' 开头？
                # 2. 是否以 '.ts' 结尾？
                if stripped_line.startswith('http://') and stripped_line.endswith('.ts'):
                    # 替换第一个 'http://' 为 'https://'
                    # 我们在原始的 'line' 上操作，以保留末尾的换行符
                    new_line = line.replace('http://', 'https://', 1)
                    new_lines.append(new_line)
                    file_links_changed += 1
                else:
                    # 如果不匹配，则原封不动地添加原始行
                    # 这会保留所有注释、标签和已经是 https 的链接
                    new_lines.append(line)

            # --- 3. 仅在有更改时才写回文件 ---
            if file_links_changed > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                print(f"  ✅ 成功：在 {file_path.name} 中替换了 {file_links_changed} 个链接。")
                total_files_changed += 1
                total_links_changed += file_links_changed
            else:
                print(f"  ℹ️ 跳过：在 {file_path.name} 中未发现需要替换的 http:// .ts 链接。")

        except Exception as e:
            print(f"  ❌ 错误：处理文件 {file_path.name} 时出错: {e}")

    print(f"\n--- ✨ 处理完成 ---")
    print(f"总共修改了 {total_files_changed} 个文件。")
    print(f"总共替换了 {total_links_changed} 个链接。")



def main():
    ensure_dir(DOWNLOAD_DIR)

    # 读取 Excel
    df = pd.read_excel(EXCEL_PATH)

    if M3U8_URL_COLUMN not in df.columns:
        raise KeyError(f"Excel 中没有找到列：{M3U8_URL_COLUMN}")

    # 准备一列存放新 URL
    new_urls = []

    for idx, row in df.iterrows():
        url = row.get(M3U8_URL_COLUMN)

        if pd.isna(url) or not isinstance(url, str) or not url.strip():
            # 如果这一行没有链接，就留空
            new_urls.append("")
            print(f"[跳过] 行 {idx}：没有有效的 m3u8 链接")
            continue

        url = url.strip()

        try:
            # 1. 生成新文件名
            new_filename = extract_new_filename_from_url(url)
            save_path = os.path.join(DOWNLOAD_DIR, new_filename)

            # 2. 下载 m3u8 文件
            print(f"[下载] 行 {idx}: {url} -> {save_path}")
            download_m3u8(url, save_path)

            # 3. 拼接新 URL
            new_url = f"{BASE_URL}/{new_filename}"
            new_urls.append(new_url)

        except Exception as e:
            # 出错时记录空字符串或错误信息
            print(f"[错误] 行 {idx} 处理失败: {e}")
            new_urls.append("")

    # 把新列加入 DataFrame
    df[NEW_URL_COLUMN] = new_urls

    # 导出新的 Excel
    df.to_excel(OUTPUT_EXCEL_PATH, index=False)
    print(f"处理完成，已写入：{OUTPUT_EXCEL_PATH}")


if __name__ == "__main__":
    #main()
    target_folder = "clip_http"
    process_m3u8_files_in_folder(target_folder)
