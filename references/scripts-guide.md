# Scripts Guide — 引擎脚本与输出适配

> 脚本的价值 = 批量、缓存、并发节流、独立复核；单点查询直接调 MCP 工具更快。**输出分层不需要跑脚本**——按下方分层原则自行适配即可。

## 引擎一览

### 选品发现 `picker.py`（Amazon）

```bash
python3 scripts/picker.py --mode newbie --platform amazon --site US --keyword "kitchen storage"
python3 scripts/picker.py --mode blueocean --platform amazon --site US --keyword "pet supplies" --profile factory
python3 scripts/picker.py --profile-help   # 卖家画像说明
```

- 卖家画像 `newbie/grower/pro/factory/brand` 只调**风险呈现的详略**（新手全表+安全清单高亮；专业折叠为脚注+🔴一行提示，`--show-risks` 展开），**永不隐藏任何产品**
- 四层风险咨询制（advisory, never blocking）：🔴hard（食品/保健品/医疗器械/功能化妆品/婴儿食品/农药/酒类——合规资质壁垒）/ 🟡capital（服装鞋包珠宝家具——资金与退货压力）/ 🟠ops（电子/液体/易燃/IP 授权——认证物流售后复杂度）/ ⚠️trap（假评论/合并评论/价格战/红海/季节性/重抛货——数据异常或饱和信号）/ 🟢safe
- `--allow-capital` / `--allow-ops` 调整警示权重（不是解封开关，默认无隐藏）；`--explicit-category` 等价于两者齐开
- 自动分析维度：品牌垄断（Top3>40% 警示）/ Amazon Basics 渗透 / 低评高销机会 / 价格战（<$10 聚集）/ 量化风险摘要（退货率、资金需求、周转天数、品牌集中度、新品存活率、价格离散度）
- 高风险常识项（配饰 5-15% 退货、眼镜 10-20%、手机壳红海、节庆装饰短窗、图书低毛利）以咨询注记呈现

### 候选复核（Go/No-Go 前必跑，双层）

```bash
# Step 0 数据核实：批量拉候选的真实 product_detail（选品表价格≠实际价）
python3 scripts/verify_candidates.py --input my_asins.txt --out verify_raw.json --brief

# Layer 1 确定性独立复核：类目相关性（关键词污染检出）/毛利合理性/IP 词/评论异常/季节窗/合规红旗 → 每品 GO/CAUTION/NO-GO
python3 scripts/review_shortlist.py shortlist.json --keyword "yoga mat"
```

**Layer 2 独立子智能体复核**（终审 Go/No-Go 必做）：起**全新上下文**的独立子 agent（不复用选品会话——新鲜上下文才有独立性），只喂 shortlist+风险徽章+Layer 1 输出，不喂选品推理；让它红队挑战 GO 结论、对照卖家画像复核，返回逐品终审。主 agent 可不认同但须记录异议。复核 informs，never deletes——没有产品因复核被移除。

### 竞品/关键词/市场 `analyst.py`（Amazon）· `walmart_analyst.py`（Walmart）

```bash
python3 scripts/analyst.py --mode competitor --platform amazon --site US --asin B07H9PZDQW
python3 scripts/analyst.py --mode keyword --platform amazon --site US --keyword "yoga mat"
python3 scripts/analyst.py --mode market --platform amazon --site US --node-id 1064954
python3 scripts/walmart_analyst.py --mode competitor --product-id 15689567602
```

### 利润测算 `calculator.py`

```bash
python3 scripts/calculator.py --platform amazon --price 29.99 --cost 8.5 --weight 1.2
```

输出毛利、盈亏平衡日销、退货率敏感性；FBA 费用按重量估算——用 product_detail 的实际尺寸重量复核。

### 监控 `monitor.py`

```bash
python3 scripts/monitor.py --mode add --type asin --value B07H9PZDQW --platform amazon --site US
python3 scripts/monitor.py --mode daily
python3 scripts/monitor.py --mode alert
```

### Walmart 选品 `walmart_picker.py`

```bash
python3 scripts/walmart_picker.py --mode blueocean --keyword "yoga mat" --profile grower
```

评论阈值 <200（Amazon 是 <500，Walmart 整体评论量更低）；自动分析 1P 自营占比、WFS 渗透；复用四层风险咨询制。

### 运维 `healthcheck.py` / `probe_endpoints.py` / `install.py` / `sync_manager.py`

环境体检 / 九端点探活+配额 / 安装 / schema 同步，各见文件头说明。

### 平台功能探索 `explorer/*.js`（Playwright）

用户问「Sorftime 有什么功能/哪些字段」时的 Web 端自动化探索。原则：一次只走一个模块；存在≠可用，要点进去验证；用勾选框选数据行（5+ 行）触发对比；每切一次 tab 存 checkpoint；`*.sorftime.com` 走 DIRECT 不走代理。

## 输出分层原则（模型自行适配，无脚本依赖）

| 用户阶段 | 输出特征 |
|---------|---------|
| 新手 beginner | 解释术语，强调「为什么重要」和「下一步做什么」 |
| 成长 growing | 突出数据变化、机会点、竞争风险提示 |
| 专业 pro | 直接结论，推荐批量/API 方案，最少铺垫 |

用户明确要求特定格式（原始表/JSON/按销量排序）时，格式跟随用户，跳过分层。

## 闭环选品工作流（显式触发才进）

**不是默认路径**。仅当用户 `/goal` / `/loop` 显式调用或明说「跑完整闭环选品工作流」时启用；日常查询永不进入。完整规范 → `references/workflows/closed-loop-selection.md`（P0→PG 七阶段、7 席卖家评审团、数据持久化、/loop 监控；进入后各阶段强制不跳步）。快速启动：

```
/goal /sorftime-seller-agent Execute Closed-Loop Product Selection for {category} on {platform}. Seller: {stage}, ${budget}, {model}, country={cn|us|uk|de|other}. Rounds: {N}.
```
