from __future__ import annotations

import os
import sys
from operator import truediv

import requests
from urllib.parse import urljoin
from pathlib import Path

from sqlalchemy import true


def read_m3u8_from_url(m3u8_url: str) -> str:
    """从 URL 读取 m3u8 内容"""
    resp = requests.get(m3u8_url, timeout=10)
    resp.raise_for_status()
    return resp.text


def read_m3u8_from_file(m3u8_path: str) -> str:
    """从本地文件读取 m3u8 内容"""
    with open(m3u8_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_ts_urls(m3u8_content: str, base: str = None):
    """
    从 m3u8 文本中解析出所有 ts 片段的 URL（或路径）
    - 忽略以 # 开头的行（注释、EXTINF 等）
    - 如果提供 base（URL 或目录），会将相对路径拼成完整 URL/路径
    """
    ts_urls = []

    for line in m3u8_content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # 如果有 base，就用 urljoin 处理相对路径；否则保留原样
        if base is not None:
            full = urljoin(base, line)
        else:
            full = line

        ts_urls.append(full)

    return ts_urls


def download_file(url: str, output_path: Path, headers=None, chunk_size: int = 8192):
    """下载单个文件到 output_path"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=15, headers=headers) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)


def download_m3u8_ts(
    m3u8_source: str,
    output_dir: str = "./ts_output",
    is_url: bool = True,
    headers: dict | None = None,
):
    """
    读取 m3u8（URL 或 本地文件），依次下载其中的 ts 片段。

    :param m3u8_source: m3u8 的 URL 或 本地路径
    :param output_dir: ts 片段保存目录
    :param is_url: True: m3u8_source 是 URL；False: 是本地文件路径
    :param headers: 请求头（如果需要带 cookie/UA 的话）
    """
    if is_url:
        print(f"[INFO] 从 URL 读取 m3u8: {m3u8_source}")
        m3u8_content = read_m3u8_from_url(m3u8_source)
        base = m3u8_source  # 用于处理相对路径
    else:
        print(f"[INFO] 从本地文件读取 m3u8: {m3u8_source}")
        m3u8_content = read_m3u8_from_file(m3u8_source)

        # 本地 m3u8 没有 URL base，只能把 ts 当“原样路径”（比如同目录下）
        # 如果你有远程 base 地址，可以自己传进来改一下这个逻辑
        base = None

    ts_urls = parse_ts_urls(m3u8_content, base)
    print(f"[INFO] 共解析出 {len(ts_urls)} 个 ts 片段")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for idx, ts_url in enumerate(ts_urls[:10], start=1):
        # 获取文件名：优先用 URL 里的名字，不行就用 index 命名
        name_from_url = os.path.basename(ts_url.split("?")[0])
        if not name_from_url or "." not in name_from_url:
            filename = f"{idx:05d}.ts"
        else:
            filename = f"{idx:05d}_{name_from_url}"

        out_path = output_dir / filename

        print(f"[{idx}/{len(ts_urls)}] 下载: {ts_url} -> {out_path}")
        try:
            download_file(ts_url, out_path, headers=headers)
        except Exception as e:
            print(f"  [ERROR] 下载失败: {e}")
            # 这里可以根据需要选择：continue / break / 重试等


if __name__ == "__main__":
    """
    命令行用法示例：

    1) 从 URL 下载：
       python download_m3u8_ts.py "https://example.com/playlist.m3u8" ./output 1

    2) 从本地 m3u8 文件下载：
       python download_m3u8_ts.py "./test.m3u8" ./output 0
    """


    m3u8_source = "https://mp2.dayilive.com/clip/1e5b3cefd6.m3u8"
    output_dir = "m3u8_test"
    is_url_flag  = true

    download_m3u8_ts(m3u8_source, output_dir, is_url=is_url_flag)
