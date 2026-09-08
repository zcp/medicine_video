// 测试标题解析功能
const testTitles = [
  "264 赵国栋教授｜机器人扩大左半肝切除术（左肝ICC，左...",
  "峰云镜会｜3D腹腔镜IIIb型肝门胆管癌根治术",
  "光头强－结直肠癌肝转移专项学习班（第2期）",
  "0522 骨科与运动康复联合文献分享会（第17期）－半月板撕裂...",
  "49期：宏光镜界微创肝胆胰膜外科中青年专家手术直播月手...",
  "0522 人工髋膝关节置换手术系列讨论之——第二期 日间髋膝...",
  "0522 胸有甲兵 术立巅峰｜南方医科大学南方医院胸外科手术..."
];

function parseTitleInfo(title) {
  console.log(`\n测试: "${title}"`);
  
  // 规则2: 使用 | 或 ｜ 分隔的格式
  const pattern2 = /([一-龥]{2,4})(教授|主任医师|副主任医师|主治医师|医师|博士)\s*[|｜]/;
  const match2 = title.match(pattern2);
  
  if (match2) {
    console.log(`✅ 成功匹配!`);
    console.log(`   专家姓名: ${match2[1]}`);
    console.log(`   专家职称: ${match2[2]}`);
    return { name: match2[1], title: match2[2], hasInfo: true };
  }
  
  // 规则1: 姓名 + 职称（紧密连接）
  const titles = ['教授', '主任医师', '副主任医师', '主治医师', '医师', '博士'];
  const titlePattern = titles.join('|');
  const pattern1 = new RegExp(`([一-龥]{2,4})\\s*(${titlePattern})`);
  const match1 = title.match(pattern1);
  
  if (match1) {
    console.log(`✅ 成功匹配 (规则1)!`);
    console.log(`   专家姓名: ${match1[1]}`);
    console.log(`   专家职称: ${match1[2]}`);
    return { name: match1[1], title: match1[2], hasInfo: true };
  }
  
  console.log(`❌ 未能提取到专家信息`);
  return { hasInfo: false };
}

console.log('=== 开始测试标题解析 ===');
testTitles.forEach(title => parseTitleInfo(title));
console.log('\n=== 测试完成 ===');
