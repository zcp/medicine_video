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
proxy = "http://127.0.0.1:1080"

CONCURRENT_USERS = 10
TEST_DURATION = 60          # 拉流时长，秒
NUM_ROUNDS = 1
INTERVAL_MINUTES = 30
MAX_TS_CHECK = 13            # 采样前几个 ts

# 请求单个 ts 的 HEAD，返回状态码和关键头部
async def fetch_head_info(url, session):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "*/*"
    }
    try:
        async with session.get(url, headers=headers) as resp:
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
        async with session.get(m3u8_url) as resp:
            if resp.status != 200:
                print(f"Warning: m3u8 请求失败，状态码 {resp.status}")
                return ts_urls
            text = await resp.text()
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and line.endswith(".ts"):
                    ts_url = urllib.parse.urljoin(m3u8_url, line)
                    ts_urls.append(ts_url)
                    if len(ts_urls) >= max_count:
                        break
    except Exception as e:
        print(f"Exception in get_ts_urls: {e}")
    return ts_urls

# 主测试逻辑，拉流 + 采集多个 ts 片段头部信息 + 计算首屏时间
async def run_ffmpeg_test(index, url, session):
    # 1. 先请求 M3U8 计时
    t0 = time.time()
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                print(f"User {index} 警告：M3U8 请求失败，状态码 {resp.status}")
            m3u8_text = await resp.text()
    except Exception as e:
        print(f"User {index} M3U8 请求异常: {e}")
        m3u8_text = ""

    m3u8_time = time.time() - t0

    # 2. 解析 TS 列表（限制前 MAX_TS_CHECK 个）
    ts_urls = []
    for line in m3u8_text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and line.endswith(".ts"):
            ts_url = urllib.parse.urljoin(url, line)
            ts_urls.append(ts_url)
            if len(ts_urls) >= MAX_TS_CHECK:
                break

    # 3. 请求第一个 TS 计时，作为首屏时间的一部分
    first_ts_time = None
    if ts_urls:
        t_start = time.time()
        first_ts_info = await fetch_head_info(ts_urls[0], session)
        first_ts_time = time.time() - t_start
    else:
        first_ts_info = None
        first_ts_time = None

    # 4. 并发请求所有 TS 头部
    tasks = [fetch_head_info(ts_url, session) for ts_url in ts_urls]
    ts_results = await asyncio.gather(*tasks)

    # 5. 启动 ffmpeg 拉流，收集 fps、speed、frame、dropped

    cmd = [
        "ffmpeg",
        "-loglevel", "info",  # 改成 info 级别，保证输出状态信息
        #"-http_proxy", proxy,
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

    # 6. 统计数据
    ts_statuses = [r["status"] for r in ts_results]
    ts_cache_hits = sum(1 for r in ts_results if r["cf_cache_status"] == "HIT")
    ts_404_count = sum(1 for s in ts_statuses if s == 404)

    # 7. 计算首屏时间 = M3U8请求时间 + 第一个TS请求时间
    first_screen_time = None
    if m3u8_time is not None and first_ts_time is not None:
        first_screen_time = round(m3u8_time + first_ts_time, 3)

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
        "first_screen_time": first_screen_time,
        "ts_details": ts_results,
    }

async def run_round(round_num, label, url):
    print(f"\n🚀 Round {round_num} - Testing [{label}]")
    connector = TCPConnector(limit=None)
    async with ClientSession(connector=connector) as session:
        tasks = [run_ffmpeg_test(i + 1, url, session) for i in range(CONCURRENT_USERS)]
        results = await asyncio.gather(*tasks)

    # 统计分析
    valid_first_screen_times = [r["first_screen_time"] for r in results if r["first_screen_time"] is not None]
    avg_first_screen = sum(valid_first_screen_times) / len(valid_first_screen_times) if valid_first_screen_times else None
    total_cache_hits = sum(r["ts_cache_hits"] for r in results)
    total_ts = sum(len(r["ts_statuses"]) for r in results)
    total_404 = sum(r["ts_404_count"] for r in results)
    cache_hit_rate = total_cache_hits / total_ts if total_ts > 0 else None
    error_rate = total_404 / total_ts if total_ts > 0 else None

    print(f"➡️ 平均首屏时间: {avg_first_screen:.3f} 秒" if avg_first_screen else "无有效首屏时间数据")
    print(f"➡️ 缓存命中率: {cache_hit_rate:.2%}" if cache_hit_rate is not None else "无缓存命中数据")
    print(f"➡️ 404 错误率: {error_rate:.2%}" if error_rate is not None else "无错误率数据")

    # 输出 CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{label}_round{round_num}_{timestamp}.csv"
    with open(output_file, "w", newline="", encoding="utf-8") as f:
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
        loop.run_until_complete(asyncio.sleep(1))
        loop.close()
