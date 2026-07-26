#!/usr/bin/env node
/**
 * checkpoint-save.js
 * 检查点保存脚本 - 标准化保存当前操作状态
 *
 * 使用方法:
 *   node checkpoint-save.js amazon keyword "ASIN反查关键词" "验证HOT标签功能" "测试HOT标签弹窗"
 *
 * 输出:
 *   保存到 progress/{platform}/{module}/checkpoint.json
 */

const fs = require('fs');
const path = require('path');

// 使用 import.meta.url 或 process.argv[1] 来获取脚本路径
const SCRIPT_PATH = process.argv[1] || __filename;
const SCRIPT_DIR = path.dirname(SCRIPT_PATH);
const SKILL_DIR = path.dirname(SCRIPT_DIR);
const PROGRESS_DIR = path.join(SKILL_DIR, 'progress');

/**
 * 生成检查点文件
 */
function saveCheckpoint(platform, module, currentSubmodule, lastOperation, nextAction, pageUrl, options = {}) {
  const checkpointDir = path.join(PROGRESS_DIR, platform, module);
  const checkpointFile = path.join(checkpointDir, 'checkpoint.json');

  // 确保目录存在
  if (!fs.existsSync(checkpointDir)) {
    fs.mkdirSync(checkpointDir, { recursive: true });
    console.log(`[Checkpoint] Created directory: ${checkpointDir}`);
  }

  const checkpoint = {
    timestamp: new Date().toISOString(),
    operator: "Claude Code",
    sessionValid: options.sessionValid !== false,
    platform: platform,
    module: module,
    currentSubmodule: currentSubmodule,
    lastOperation: lastOperation,
    nextAction: nextAction,
    pageUrl: pageUrl || null,
    navigationType: options.navigationType || "unknown",
    lastError: options.lastError || null,
    progressPercent: options.progressPercent || 0,
    notes: options.notes || []
  };

  fs.writeFileSync(checkpointFile, JSON.stringify(checkpoint, null, 2));
  console.log(`[Checkpoint] Saved to: ${checkpointFile}`);
  console.log(`[Checkpoint] Last operation: ${lastOperation}`);
  console.log(`[Checkpoint] Next action: ${nextAction}`);

  return checkpoint;
}

/**
 * 读取检查点
 */
function loadCheckpoint(platform, module) {
  const checkpointFile = path.join(PROGRESS_DIR, platform, module, 'checkpoint.json');

  if (!fs.existsSync(checkpointFile)) {
    console.log(`[Checkpoint] No checkpoint found for ${platform}/${module}`);
    return null;
  }

  const checkpoint = JSON.parse(fs.readFileSync(checkpointFile, 'utf8'));
  console.log(`[Checkpoint] Loaded from: ${checkpointFile}`);
  console.log(`[Checkpoint] Timestamp: ${checkpoint.timestamp}`);
  console.log(`[Checkpoint] Last operation: ${checkpoint.lastOperation}`);
  console.log(`[Checkpoint] Next action: ${checkpoint.nextAction}`);

  return checkpoint;
}

/**
 * 清除检查点
 */
function clearCheckpoint(platform, module) {
  const checkpointFile = path.join(PROGRESS_DIR, platform, module, 'checkpoint.json');

  if (fs.existsSync(checkpointFile)) {
    fs.unlinkSync(checkpointFile);
    console.log(`[Checkpoint] Cleared: ${checkpointFile}`);
  }
}

/**
 * 更新进度百分比
 */
function updateProgress(platform, module, completedCount, totalCount) {
  const progressFile = path.join(PROGRESS_DIR, platform, module, 'progress.json');

  if (!fs.existsSync(progressFile)) {
    console.log(`[Progress] No progress file found: ${progressFile}`);
    return null;
  }

  const progress = JSON.parse(fs.readFileSync(progressFile, 'utf8'));
  const percent = Math.round((completedCount / totalCount) * 100);

  progress.lastUpdated = new Date().toISOString();
  progress.progressPercent = percent;

  fs.writeFileSync(progressFile, JSON.stringify(progress, null, 2));
  console.log(`[Progress] Updated: ${percent}% (${completedCount}/${totalCount})`);

  return progress;
}

// CLI 入口
function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case 'save':
      // node checkpoint-save.js save amazon keyword "ASIN反查关键词" "验证HOT标签" "测试弹窗" "https://..."
      saveCheckpoint(args[1], args[2], args[3], args[4], args[5], args[6], {
        navigationType: args[7] || 'goto',
        progressPercent: parseInt(args[8]) || 0
      });
      break;

    case 'load':
      // node checkpoint-save.js load amazon keyword
      loadCheckpoint(args[1], args[2]);
      break;

    case 'clear':
      // node checkpoint-save.js clear amazon keyword
      clearCheckpoint(args[1], args[2]);
      break;

    case 'progress':
      // node checkpoint-save.js progress amazon keyword 5 10
      updateProgress(args[1], args[2], parseInt(args[3]), parseInt(args[4]));
      break;

    default:
      console.log(`
checkpoint-save.js - 检查点保存工具

用法:
  node checkpoint-save.js save <platform> <module> <submodule> <lastOp> <nextAction> [pageUrl] [navType] [progress]

  node checkpoint-save.js load <platform> <module>

  node checkpoint-save.js clear <platform> <module>

  node checkpoint-save.js progress <platform> <module> <completed> <total>

示例:
  node checkpoint-save.js save amazon keyword "ASIN反查关键词" "验证HOT标签功能" "测试弹窗" "https://seller.sorftime.com/home/asinkeyword"
      `);
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  saveCheckpoint,
  loadCheckpoint,
  clearCheckpoint,
  updateProgress
};
