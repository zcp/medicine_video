import asyncio
import csv
import re
import time
import urllib.parse
from datetime import datetime
from aiohttp import ClientSession, TCPConnector

# 配置项
VIDEO_URLS = {
    "cdn": "https://lancet.im/videos/hls/1888844408_82b2/hls/video_1888844408_82b2_local_20250912T191436.m3u8",
    "r2": "https://pub-8ea55317b8624238a35e5c73454b9d2d.r2.dev/videos/hls/1888844408_82b2/hls/video_1888844408_82b2_local_20250912T191436.m3u8",
}

#proxy = "socks5://127.0.0.1:1080"
proxy = None

CONCURRENT_USERS = 2
TEST_DURATION = 15           # 拉流时长，秒
NUM_ROUNDS = 1
INTERVAL_MINUTES = 30
MAX_TS_CHECK = 5            # 采样前几个 ts

# 请求单个 ts 的 HEAD，返回状态码和关键头部
async def fetch_head_info(url, session):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*"
    }
    try:
        async with session.get(url, headers=headers, proxy=proxy) as resp:
            # 不读取内容，只取 header
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return {
                "status": resp.status,
                "cf_cache_status": headers.get("cf-cache-status", "N/A"),
                "cf_ray": headers.get("cf-ray", "N/A"),
                "url": url
            }
    except Exception as e:
        return {"status": 0, "cf_cache_status": "ERROR", "cf_ray": "ERROR", "url": url}

# 解析 m3u8 获取 TS 片段完整 URL 列表
async def get_ts_urls(m3u8_url, session, max_count=MAX_TS_CHECK):
    ts_urls = []
    try:
        #print("1")
        async with session.get(m3u8_url, proxy=proxy) as resp:
            #print("2")
            if resp.status != 200:
                print(f"Warning: m3u8 请求失败，状态码 {resp.status}")
                return ts_urls
            text = await resp.text()
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and line.endswith(".ts"):
                    # 拼接绝对URL
                    ts_url = urllib.parse.urljoin(m3u8_url, line)
                    #print("ts_url",ts_url)
                    ts_urls.append(ts_url)
                    if len(ts_urls) >= max_count:
                        #ts_urls = ["https://lancet.im/videos/hls/ts/880955976765-3-602540_2006_4_d0_mb220207_sb220207.ts"]
                        break
    except Exception as e:
        print(f"Exception in get_ts_urls: {e}")
    return ts_urls

# 主测试逻辑，拉流 + 采集多个 ts 片段头部信息
async def run_ffmpeg_test(index, url, session):
    cmd = [
        "ffmpeg",
        "-loglevel", "debug",  # 👈 输出详细信息用于调试
        "-http_proxy", proxy,  # 👈 强制走代理
        "-i", url,
        "-t", str(TEST_DURATION),
        "-f", "null", "-"
    ]

    start_time = time.time()
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    duration = time.time() - start_time

    stderr_decoded = stderr.decode()
    speed_match = re.findall(r"speed=\s*([\d\.]+)x", stderr_decoded)
    fps_match = re.findall(r"fps=\s*(\d+)", stderr_decoded)
    frame_match = re.findall(r"frame=\s*(\d+)", stderr_decoded)
    drop_match = re.findall(r"drop.*?=\s*(\d+)", stderr_decoded)

    # 解析多个TS
    ts_urls = await get_ts_urls(url, session)
    ts_results = []
    for ts_url in ts_urls:
        start_ts = time.time()
        head_info = await fetch_head_info(ts_url, session)
        head_info["elapsed"] = round(time.time() - start_ts, 3)
        ts_results.append(head_info)

    # 简单统计
    ts_statuses = [r["status"] for r in ts_results]
    ts_cache_hits = sum(1 for r in ts_results if r["cf_cache_status"] == "HIT")
    ts_404_count = sum(1 for s in ts_statuses if s == 404)

    return {
        "user": index,
        "start_time": datetime.now().isoformat(),
        "duration_s": round(duration, 2),
        "speed": float(speed_match[-1]) if speed_match else None,
        "fps": int(fps_match[-1]) if fps_match else None,
        "frames": int(frame_match[-1]) if frame_match else None,
        "dropped": int(drop_match[-1]) if drop_match else 0,
        "return_code": proc.returncode,
        "ts_statuses": ts_statuses,
        "ts_cache_hits": ts_cache_hits,
        "ts_404_count": ts_404_count,
        "ts_details": ts_results,
    }

async def run_round(round_num, label, url):
    print(f"\n🚀 Round {round_num} - Testing [{label}]")
    connector = TCPConnector(limit=None)
    async with ClientSession(connector=connector) as session:
        tasks = [run_ffmpeg_test(i + 1, url, session) for i in range(CONCURRENT_USERS)]
        results = await asyncio.gather(*tasks)

    # 输出 CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{label}_round{round_num}_{timestamp}.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        # 扩展字段 ts_details 序列化为字符串
        fieldnames = list(results[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            r["ts_details"] = str(r["ts_details"])
            writer.writerow(r)
    print(f"✅ 结果已保存至: {output_file}")

async def run_all_rounds():
    for round_num in range(1, NUM_ROUNDS + 1):
        for label, url in VIDEO_URLS.items():
            await run_round(round_num, label, url)
        if round_num < NUM_ROUNDS:
            print(f"⏳ 等待 {INTERVAL_MINUTES} 分钟进行下一轮测试...\n")
            await asyncio.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
        import warnings

        warnings.filterwarnings("ignore", category=RuntimeWarning)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_all_rounds())
        finally:
            loop.run_until_complete(asyncio.sleep(1))  # 让 __del__ 有机会跑完
            loop.close()

