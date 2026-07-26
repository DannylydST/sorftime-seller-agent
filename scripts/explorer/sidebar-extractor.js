#!/usr/bin/env node
/**
 * sidebar-extractor.js
 * 侧边栏导航提取脚本 - 提取所有侧边栏链接并分类
 *
 * 使用方法:
 *   在 playwright-cli eval 中执行提取逻辑
 */

const extractSidebarScript = `
// 提取侧边栏所有链接
function extractSidebar() {
  const sidebar = document.querySelector('.sorftimeAside-nav');
  if (!sidebar) return { error: 'sidebar not found' };

  const links = sidebar.querySelectorAll('a');
  const nav = [];

  links.forEach(a => {
    const text = a.innerText.trim();
    const href = a.getAttribute('href') || 'NO_HREF';
    const isClickNav = !href || href === 'NO_HREF';

    nav.push({
      text: text,
      href: href,
      type: isClickNav ? 'click' : 'href',
      module: categorizeModule(text)
    });
  });

  return {
    total: nav.length,
    hrefModules: nav.filter(n => n.type === 'href'),
    clickModules: nav.filter(n => n.type === 'click'),
    all: nav
  };
}

function categorizeModule(text) {
  const categories = {
    '看板': ['市场看板', '产品看板', '关键词看板', '卖家看板', '品牌看板', '达人看板', '视频看板'],
    '报告': ['类目报告', '竞争分析'],
    '榜单': ['畅销榜', 'Best Seller'],
    '工具': ['查专利', '侵权预警', '监控', '工具', '插件']
  };

  for (const [cat, keywords] of Object.entries(categories)) {
    for (const kw of keywords) {
      if (text.includes(kw)) return cat;
    }
  }
  return '其他';
}

JSON.stringify(extractSidebar(), null, 2);
`;

console.log('=== 侧边栏提取脚本 ===');
console.log('\n在 playwright-cli 中执行:');
console.log(`playwright-cli eval "() => { ${extractSidebarScript} }"`);

console.log('\n=== 预期输出格式 ===');
console.log(JSON.stringify({
  total: 9,
  hrefModules: [
    { text: '首页', href: '/home', type: 'href', module: '其他' },
    { text: '类目报告', href: '/home/flow', type: 'href', module: '报告' }
  ],
  clickModules: [
    { text: '市场看板', href: 'NO_HREF', type: 'click', module: '看板' }
  ]
}, null, 2));

module.exports = { extractSidebarScript };
