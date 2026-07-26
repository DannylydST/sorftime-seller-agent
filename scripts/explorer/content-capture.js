#!/usr/bin/env node
/**
 * content-capture.js
 * 标准化内容捕获脚本 - 捕获 Sorftime 页面结构和内容
 *
 * 使用方法:
 *   playwright-cli eval "() => { ${require('./content-capture.js').capturePage.toString().replace('export ', '')}() }"
 *
 * 或在 Node.js 环境中:
 *   const { capturePage, captureTable, captureDialog, captureModal } = require('./content-capture.js');
 */

/**
 * 捕获页面整体结构
 * @returns {Object} 页面结构对象
 */
function capturePage() {
  return {
    url: window.location.href,
    title: document.title,
    timestamp: new Date().toISOString(),
    sidebar: captureSidebar(),
    mainContent: captureMainContent(),
    dialogs: captureDialogs(),
    buttons: captureButtons(),
    inputs: captureInputs()
  };
}

/**
 * 捕获侧边栏导航
 */
function captureSidebar() {
  const sidebar = document.querySelector('.sorftimeAside-nav');
  if (!sidebar) return { error: 'sidebar not found' };

  const items = sidebar.querySelectorAll('.sorftimeAside-nav__list');
  const nav = [];

  items.forEach(item => {
    const a = item.querySelector('a');
    const text = item.innerText.trim();
    const href = a ? (a.getAttribute('href') || 'NO_HREF') : 'NO_A_TAG';

    nav.push({
      text: text,
      href: href,
      type: href === 'NO_HREF' || href === 'NO_A_TAG' ? 'click' : 'href',
      module: categorizeModule(text)
    });
  });

  return { total: nav.length, items: nav };
}

/**
 * 捕获主内容区域
 */
function captureMainContent() {
  // 尝试多种选择器
  const selectors = [
    '.main-content',
    '.content-wrapper',
    '[class*=main]',
    'main',
    '.router-view',
    '#app'
  ];

  let content = null;
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el && el.innerText.length > 100) {
      content = {
        selector: sel,
        textLength: el.innerText.length,
        text: el.innerText.substring(0, 1000).replace(/\s+/g, ' ').trim()
      };
      break;
    }
  }

  return content || { error: 'main content not found' };
}

/**
 * 捕获表格数据
 * @param {string} tableSelector - 表格选择器 (可选)
 */
function captureTable(tableSelector) {
  const tables = document.querySelectorAll('table, [class*=table]');
  if (tables.length === 0) return { error: 'no tables found' };

  const results = [];
  tables.forEach((table, idx) => {
    if (tableSelector && !table.matches(tableSelector)) return;

    const rows = table.querySelectorAll('tr');
    const headers = [];
    const headerCells = table.querySelectorAll('th');
    headerCells.forEach(th => headers.push(th.innerText.trim()));

    const data = [];
    rows.forEach((row, rowIdx) => {
      if (rowIdx === 0) return; // skip header row
      const cells = row.querySelectorAll('td');
      if (cells.length > 0) {
        const rowData = {};
        cells.forEach((cell, cellIdx) => {
          const key = headers[cellIdx] || `col_${cellIdx}`;
          rowData[key] = cell.innerText.trim().substring(0, 50);
        });
        data.push(rowData);
      }
    });

    if (data.length > 0) {
      results.push({
        index: idx,
        rowCount: data.length,
        headers: headers,
        firstRows: data.slice(0, 5)
      });
    }
  });

  return results;
}

/**
 * 捕获所有按钮
 */
function captureButtons() {
  const btns = document.querySelectorAll('button');
  const buttonTexts = [];
  btns.forEach(b => {
    const text = b.innerText.trim();
    if (text && text.length < 30) {
      buttonTexts.push({
        text: text,
        disabled: b.disabled,
        className: b.className.substring(0, 30)
      });
    }
  });

  // 去重
  const unique = [];
  const seen = new Set();
  buttonTexts.forEach(btn => {
    if (!seen.has(btn.text)) {
      seen.add(btn.text);
      unique.push(btn);
    }
  });

  return unique;
}

/**
 * 捕获所有输入框
 */
function captureInputs() {
  const inputs = document.querySelectorAll('input, textarea, [class*=input]');
  const results = [];

  inputs.forEach((input, idx) => {
    const tag = input.tagName.toLowerCase();
    const type = input.type || 'text';
    const placeholder = input.placeholder || input.getAttribute('placeholder') || '';
    const value = input.value || '';

    if (placeholder || type !== 'hidden') {
      results.push({
        index: idx,
        tag: tag,
        type: type,
        placeholder: placeholder.substring(0, 50),
        value: value.substring(0, 50)
      });
    }
  });

  return results;
}

/**
 * 捕获弹窗/对话框
 */
function captureDialogs() {
  const dialogs = document.querySelectorAll('.el-dialog, [class*=dialog]');
  const results = [];

  dialogs.forEach(dialog => {
    // 检查是否可见
    const isVisible = dialog.offsetParent !== null ||
                       dialog.matches('.el-dialog--visible');

    if (isVisible || dialog.matches('[class*=dialog]')) {
      const titleEl = dialog.querySelector('.el-dialog__title, [class*=title]');
      const bodyEl = dialog.querySelector('.el-dialog__body, [class*=body]');

      results.push({
        className: dialog.className.substring(0, 50),
        visible: isVisible,
        title: titleEl ? titleEl.innerText.substring(0, 100) : '',
        bodyText: bodyEl ? bodyEl.innerText.substring(0, 300).replace(/\s+/g, ' ').trim() : '',
        buttons: captureDialogButtons(dialog)
      });
    }
  });

  return results;
}

/**
 * 捕获对话框内的按钮
 */
function captureDialogButtons(dialog) {
  const btns = dialog.querySelectorAll('button');
  const texts = [];
  btns.forEach(b => {
    const t = b.innerText.trim();
    if (t) texts.push(t);
  });
  return [...new Set(texts)];
}

/**
 * 捕获弹窗内容（简化版，用于 eval）
 */
function captureModal() {
  const dialogs = document.querySelectorAll('.el-dialog');
  if (dialogs.length === 0) return { hasModal: false };

  const visible = Array.from(dialogs).find(d => d.offsetParent !== null);
  if (!visible) return { hasModal: false };

  const body = visible.querySelector('.el-dialog__body');
  const title = visible.querySelector('.el-dialog__title');

  return {
    hasModal: true,
    title: title ? title.textContent : '',
    text: body ? body.innerText.substring(0, 500).replace(/\s+/g, ' ').trim() : '',
    buttonCount: visible.querySelectorAll('button').length
  };
}

/**
 * 捕获可点击的 span 元素（el-tooltip 类型的按钮）
 */
function captureClickableSpans() {
  const spans = document.querySelectorAll('span');
  const clickables = [];

  spans.forEach(span => {
    if (span.className.includes('el-tooltip') && span.children.length === 0) {
      const text = span.innerText.trim();
      if (text && text.length < 20) {
        clickables.push({
          text: text,
          className: span.className.substring(0, 40)
        });
      }
    }
  });

  return [...new Set(clickables.map(c => c.text))].map(text => ({
    text,
    className: clickables.find(c => c.text === text).className
  }));
}

/**
 * 捕获下拉选择器
 */
function captureSelects() {
  const selects = document.querySelectorAll('select');
  const results = [];

  selects.forEach((sel, idx) => {
    const options = Array.from(sel.options).map(opt => opt.text);
    results.push({
      index: idx,
      value: sel.value,
      options: options.slice(0, 10) // 最多10个选项
    });
  });

  return results;
}

/**
 * 分类模块
 */
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

// 导出
module.exports = {
  capturePage,
  captureTable,
  captureDialogs,
  captureModal,
  captureButtons,
  captureInputs,
  captureClickableSpans,
  captureSelects,
  captureSidebar
};

// 快速使用 - 捕获页面摘要
if (require.main === module) {
  console.log('=== Content Capture Script ===');
  console.log('在 playwright-cli eval 中使用:');
  console.log('() => { const cc = ' + capturePage.toString() + '; return cc(); }');
}
