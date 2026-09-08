'use strict';
const crypto = require('crypto');

// 与后端约定的 PSK（pre-shared key），需在 uniCloud 云函数环境变量中配置
// 设置方法：uniCloud 控制台 → 云函数 → get-phone-number → 环境变量 → UNIVERIFY_PSK

exports.main = async (event, context) => {
  
  // 安全要求：禁止硬编码密钥兜底；未配置 UNIVERIFY_PSK 时直接返回错误
  const PSK = process.env.UNIVERIFY_PSK;
  try {
    // 1. 调用官方接口解密手机号
    const res = await uniCloud.getPhoneNumber({
      provider: 'univerify',
      appid: context.APPID,
      access_token: event.access_token,
      openid: event.openid
    });

    const maskedRes = { ...res, phoneNumber: res.phoneNumber ? res.phoneNumber.slice(0, 3) + '****' + res.phoneNumber.slice(-4) : res.phoneNumber };
    console.log('【一键登录】解密结果：', maskedRes);

    if (res.code !== 0) {
      return { code: 1, msg: '手机号解密失败', detail: res };
    }

    if (!PSK) {
      console.error('【一键登录】UNIVERIFY_PSK 未配置，无法生成签名');
      return { code: 2, msg: '服务端配置错误，请联系管理员' };
    }

    // 2. 生成 HMAC 签名，供后端验证手机号真实来源
    const phone = res.phoneNumber;
    const timestamp = Date.now();
    const sign = crypto
      .createHmac('sha256', PSK)
      .update(phone + timestamp)
      .digest('hex');

    console.log('【一键登录】签名生成成功', { phone: phone.slice(0, 3) + '****' + phone.slice(-4), timestamp, sign: sign.substring(0, 16) + '...' });

    // 3. 返回签名后的数据，前端转发给后端
    return {
      code: 0,
      msg: '解密并签名成功',
      phone: phone,
      sign: sign,
      timestamp: String(timestamp)   // 转字符串，后端 Pydantic 要求 string 类型
    };

  } catch (err) {
    console.error('【一键登录】云函数异常:', err.message);
    return {
      code: 500,
      msg: '运营商解密失败',
      error: err.message
    };
  }
};