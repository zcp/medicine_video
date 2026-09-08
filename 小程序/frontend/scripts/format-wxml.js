const fs = require('fs');
const path = require('path');

/**
 * 格式化WXML文件，添加换行和缩进
 * 这个脚本会扫描dist目录下的所有.wxml文件并格式化它们
 */

// WXML格式化函数
function formatWXML(content) {
  // 移除多余的空格和换行
  content = content.replace(/>\s+</g, '><');
  
  // 在标签间添加换行
  content = content.replace(/></g, '>\n<');
  
  // 添加缩进
  const lines = content.split('\n');
  let indentLevel = 0;
  const indentChar = '  '; // 两个空格缩进
  
  const formattedLines = lines.map(line => {
    const trimmedLine = line.trim();
    if (!trimmedLine) return '';
    
    // 减少缩进（闭合标签）
    if (trimmedLine.startsWith('</')) {
      indentLevel = Math.max(0, indentLevel - 1);
    }
    
    const formattedLine = indentChar.repeat(indentLevel) + trimmedLine;
    
    // 增加缩进（开启标签，但不是自闭合标签）
    if (trimmedLine.startsWith('<') && 
        !trimmedLine.startsWith('</') && 
        !trimmedLine.endsWith('/>')) {
      indentLevel++;
    }
    
    return formattedLine;
  });
  
  return formattedLines.join('\n');
}

// 递归查找所有.wxml文件
function findWXMLFiles(dir) {
  const files = [];
  const items = fs.readdirSync(dir);
  
  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      files.push(...findWXMLFiles(fullPath));
    } else if (item.endsWith('.wxml')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

// 主函数
function main() {
  const distDir = path.join(__dirname, '../dist/dev/mp-weixin');
  
  if (!fs.existsSync(distDir)) {
    console.log('❌ 找不到构建目录:', distDir);
    console.log('请先运行 npm run dev:mp-weixin 构建项目');
    return;
  }
  
  try {
    const wxmlFiles = findWXMLFiles(distDir);
    
    if (wxmlFiles.length === 0) {
      console.log('❌ 没有找到 .wxml 文件');
      return;
    }
    
    console.log(`📝 找到 ${wxmlFiles.length} 个 WXML 文件，开始格式化...`);
    
    wxmlFiles.forEach(filePath => {
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        const formatted = formatWXML(content);
        fs.writeFileSync(filePath, formatted, 'utf8');
        
        const relativePath = path.relative(distDir, filePath);
        console.log(`✅ 已格式化: ${relativePath}`);
      } catch (error) {
        console.error(`❌ 格式化失败: ${filePath}`, error.message);
      }
    });
    
    console.log('\n🎉 WXML文件格式化完成！');
    console.log('💡 提示：每次重新构建后需要重新运行此脚本');
    
  } catch (error) {
    console.error('❌ 脚本执行失败:', error.message);
  }
}

// 运行脚本
main();
