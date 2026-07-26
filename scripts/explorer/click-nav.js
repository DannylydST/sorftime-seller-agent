#!/usr/bin/env node
/**
 * click-nav.js
 * 点击导航脚本 - 用于触发 NO_HREF 类型的 Vue Router 编程式导航
 *
 * 使用方法:
 *   node click-nav.js "目标模块名称"
 *
 * 示例:
 *   node click-nav.js "市场看板"
 */

const path = require('path');

// 从命令行参数获取目标模块名称
const targetModule = process.argv[2];

if (!targetModule) {
  console.error('用法: node click-nav.js "目标模块名称"');
  console.error('示例: node click-nav.js "市场看板"');
  process.exit(1);
}

/**
 * 在浏览器控制台执行的导航逻辑
 * 使用 playwright-cli eval 调用
 */
const clickNavScript = `
function clickNavModule(moduleName) {
  const items = document.querySelectorAll('.sorftimeAside-nav__list');
  for (const item of items) {
    if (item.innerText.includes(moduleName)) {
      const a = item.querySelector('a');
      if (a) {
        a.click();
        return { success: true, module: moduleName };
      }
      return { success: false, error: 'no <a> found' };
    }
  }
  return { success: false, error: 'module not found' };
}

clickNavModule('${targetModule}');
`;

console.log(`[ClickNav] 目标模块: ${targetModule}`);
console.log(`[ClickNav] 生成脚本: ${clickNavScript.substring(0, 100)}...`);

// 输出实际可用的命令
console.log('\n=== 在 playwright-cli 中执行 ===');
console.log(`playwright-cli eval "() => { ${clickNavScript} }"`);

console.log('\n=== 或者在浏览器控制台直接执行 ===');
console.log(clickNavScript);

// 如果被 require，则导出函数
if (require.main === module) {
  console.log('\n[ClickNav] 此脚本需要在 playwright-cli 环境中执行');
  console.log('[ClickNav] 将导航逻辑复制到剪贴板...');
}

// 导出给其他模块使用
module.exports = {
  clickNavScript,
  targetModule
};
