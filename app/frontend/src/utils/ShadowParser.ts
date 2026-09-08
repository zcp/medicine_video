/**
 * ShadowParser - m3u8播放列表解析器
 * 用于uni-app原生video组件，实现TS切片检测和上报
 */

interface Segment {
  name: string;        // TS文件名（如：43811948589-3-127088_1984_1631_d0.ts）
  url: string;         // 完整URL
  start: number;       // 开始时间（秒）
  end: number;         // 结束时间（秒）
  duration: number;    // 时长（秒）
  index: number;       // 索引
}

export class ShadowParser {
  private m3u8Url: string;
  private baseUrl: string;
  private segments: Segment[] = [];
  private currentTs: string | null = null;
  private isLive: boolean = false;
  private refreshTimer: number | null = null;

  constructor(m3u8Url: string) {
    this.m3u8Url = m3u8Url;
    this.baseUrl = this.extractBaseUrl(m3u8Url);
  }

  /**
   * 初始化解析器
   */
  async init(): Promise<void> {
    await this.fetchM3u8();
    // parseContent 已在 fetchM3u8 中调用，这里不需要再次调用
    if (this.isLive) {
      this.startRefreshTimer();
    }
  }

  /**
   * 销毁解析器
   */
  destroy(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * 根据播放时间检测当前切片
   * @param currentTime 当前播放时间（秒）
   * @returns 当前切片信息或null
   */
  check(currentTime: number): Segment | null {
    // 2秒容忍度，避免边界问题
    const tolerance = 2.0;

    const segment = this.segments.find(seg =>
      currentTime >= seg.start - tolerance && currentTime < seg.end + tolerance
    );

    if (segment && segment.name !== this.currentTs) {
      this.currentTs = segment.name;
      return segment;
    }

    return null;
  }

  /**
   * 获取所有切片信息（调试用）
   */
  getSegments(): Segment[] {
    return [...this.segments];
  }

  /**
   * 提取基础URL
   */
  private extractBaseUrl(url: string): string {
    const urlObj = new URL(url);
    return `${urlObj.protocol}//${urlObj.host}${urlObj.pathname.substring(0, urlObj.pathname.lastIndexOf('/') + 1)}`;
  }

  /**
   * 获取m3u8内容
   */
  private async fetchM3u8(): Promise<void> {
    try {
      const response = await uni.request({
        url: this.m3u8Url,
        method: 'GET',
        timeout: 10000,
        // 🔧 增强容错：SSL证书验证关闭（App端）
        sslVerify: false,
        // 🔧 增强容错：处理CORS问题
        header: {
          'Accept': 'application/vnd.apple.mpegurl, application/x-mpegURL, */*',
          'Cache-Control': 'no-cache'
        }
      });

      if (response.statusCode === 200) {
        // 类型断言：确保 response.data 是 string 类型
        const content = typeof response.data === 'string' ? response.data : String(response.data);
        this.parseContent(content);
      } else {
        throw new Error(`HTTP ${response.statusCode}`);
      }
    } catch (error) {
      console.error('[ShadowParser] 获取m3u8失败:', error);

      // 🔧 增强容错：CORS错误处理
      const err = error as any;
      if (err.errMsg && err.errMsg.includes('CORS')) {
        console.warn('[ShadowParser] 检测到CORS限制，播放器仍可正常播放，但切片检测功能受限');
        // 不抛出错误，允许播放器继续工作
        return;
      }

      throw error;
    }
  }

  /**
   * 解析m3u8内容
   */
  private parseContent(content: string): void {
    if (!content || typeof content !== 'string') {
      throw new Error('Invalid m3u8 content');
    }

    const lines = content.split('\n').filter(line => line.trim());
    let currentTime = 0;
    let segmentIndex = 0;
    let mediaSequence = 0;

    // 清空之前的数据
    this.segments = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // 检测是否为直播流
      if (line.includes('#EXT-X-PLAYLIST-TYPE:VOD')) {
        this.isLive = false;
      } else if (line.includes('#EXT-X-ENDLIST')) {
        this.isLive = false;
      }

      // 处理媒体序列号
      if (line.startsWith('#EXT-X-MEDIA-SEQUENCE:')) {
        mediaSequence = parseInt(line.split(':')[1]) || 0;
      }

      // 处理片段信息
      if (line.startsWith('#EXTINF:')) {
        const duration = parseFloat(line.split(':')[1].split(',')[0]);
        const nextLine = lines[i + 1]?.trim();

        if (nextLine && !nextLine.startsWith('#')) {
          const tsName = this.extractTsName(nextLine);
          const fullUrl = this.resolveUrl(nextLine);

          this.segments.push({
            name: tsName,
            url: fullUrl,
            start: currentTime,
            end: currentTime + duration,
            duration,
            index: segmentIndex++
          });

          currentTime += duration;
        }
      }
    }

    // 如果没有明确标记，默认认为是直播流
    if (!this.segments.length) {
      this.isLive = true;
    }

    console.log(`[ShadowParser] 解析完成: ${this.segments.length}个切片, ${this.isLive ? '直播' : '点播'}模式`);
  }

  /**
   * 提取TS文件名
   */
  private extractTsName(url: string): string {
    if (url.startsWith('http')) {
      return url.split('/').pop() || '';
    }
    return url.split('/').pop() || '';
  }

  /**
   * 解析URL（处理相对路径）
   */
  private resolveUrl(url: string): string {
    if (url.startsWith('http')) {
      return url;
    }
    return `${this.baseUrl}/${url}`.replace(/\/+/g, '/');
  }

  /**
   * 启动定时刷新（直播流）
   */
  private startRefreshTimer(): void {
    // 每30秒重新获取m3u8（直播流可能有新切片）
    this.refreshTimer = setInterval(async () => {
      try {
        await this.fetchM3u8();
        console.log('[ShadowParser] 直播流m3u8已刷新');
      } catch (error) {
        console.error('[ShadowParser] 刷新m3u8失败:', error);
      }
    }, 30000) as unknown as number;
  }
}
