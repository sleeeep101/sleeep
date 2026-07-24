# 03_daily_paper_radar — 每日论文雷达

固化每日论文检索+评分+日报+知识卡片流程。

**已有现成脚本**: `<LOCAL_PATH>`，不再重建。

## 论文来源（当前阶段）

当前阶段只使用外网免费可读、可下载或开放访问的论文。不依赖复杂 API 或付费数据库。

**推荐来源**：arXiv · Google Scholar 开放 PDF · DOAJ · MDPI · Frontiers · SpringerOpen · PLOS · Remote Sensing 等开放期刊 · EarthArXiv · SSRN · 作者主页 · 机构知识库 · 其他合法开放来源

**来源原则**：
1. 优先找能直接阅读全文或下载 PDF 的论文
2. 只能看到摘要 → 必须标注「仅基于摘要」
3. 不使用盗版来源
4. 不自动批量下载论文
5. 不编造 DOI、链接、期刊、作者、年份
6. DOI 不确定 → 写「DOI：未确认」
7. 无 DOI → 保留 arXiv ID、URL 或其他稳定链接
8. 每篇论文记录来源和可访问状态

**论文类型优先级**：
1. GIS/遥感/空间分析相关开放论文
2. DEM/数字地形分析/土壤侵蚀/地貌/流域相关论文
3. 遥感分类/土地利用变化/自然资源监测/GEE 相关论文
4. GeoAI/机器学习/深度学习/时间序列/空间统计等可迁移方法论文
5. 城市研究/生态环境/风险评估/空间计量等可与 GIS 交叉的论文
6. AI Code/Baseline/消融实验/可复现实验相关论文

**找不到高质量论文时的原则**：宁可少读，不强行凑数。不推荐低质量论文。

## 自动化流程

```
每天 12:00 (Windows Task: DailyPaperCurator_1200)
  → 按轮换方向检索外网免费论文 (8方向 × 4关键词，arXiv + Semantic Scholar)
  → 优先选择可直接阅读 PDF 或开放全文的论文
  → 记录标题、作者、年份、来源、DOI/arXiv ID/URL、开放状态
  → SQLite 去重 (DOI > arXiv ID > 标题相似度)
  → 评分排序 (8维 rubric)
  → 初筛 5-10 篇候选
  → 精选 TOP 1-3 篇生成知识卡片
  → 追加长期知识库 (DOI去重)
  → 微信推送 (PushPlus Markdown 排版)
```

当前流程不依赖复杂接口或 MCP 工具。后续用户自己可下载中文论文后，手动提供给工作流处理。arXiv + Semantic Scholar API 为当前主力数据源，仅用于检索公开元数据。

## 微信推送排版

**推送方式**: PushPlus (pushplus.plus)，通过 Windows Task `DailyPaperCurator_1200` 每日 12:00 触发 `run_paper_curator.bat --push`

**推送内容** (`daily_paper_curator.py::push_wechat()`):
```
📅 日期 周X · 论文日报
━━━ 📊 今日统计 ━━━
候选 X 篇　精选 X 篇
━━━ 📄 精选论文 ━━━
1. 论文标题
   ⭐ 评分 | 来源
   一句话摘要
2. ...
━━━ 📎 ━━━
📋 完整日报: YYYY-MM-DD_论文阅读日报.md
```

**排版原则**:
- PushPlus `template: "markdown"` 模式渲染
- 手机端适配：标题 ≤ 80 字符、摘要 ≤ 120 字符
- 总分 ≤ 1900 字符（PushPlus 单条限制）
- 分隔线用 `━━━` 提升可读性
- 评分用 ⭐ 直观展示论文质量

**配置文件**: `<LOCAL_PATH>`
```json
{"pushplus_token": "your_token_here"}
```

## 8 个搜索方向轮换

| 方向 | 示例关键词 |
|------|-----------|
| DEM与地形分析 | DEM terrain analysis, digital elevation model erosion, geomorphology ML |
| GIS空间建模 | GIS spatial modeling, spatial data science Python, geospatial AI, WebGIS |
| 遥感与土地利用 | remote sensing land use, sentinel DL, GEE land cover, hyperspectral |
| 机器学习迁移 | causal inference spatial, time series forecasting, transfer learning RS |
| 生态与自然资源 | ecosystem service GIS, soil erosion, watershed analysis |
| 实验设计与方法 | indicator system, quantitative methodology GIS, uncertainty quantification |
| AI与编程工具 | AI agent coding, LLM scientific research, Python geospatial pipeline |
| 社会与交叉学科 | urban heat island, climate adaptation GIS, environmental justice spatial |

## 评分公式 (8 维 rubric)

```
总分 = GIS相关性×0.4 + 方法可迁移性×0.25 + 复现可行性×0.15 + 可读性×0.1 + 新颖性×0.1
```

每维 1-10 分。候选论文按总分排序，TOP 10 入日报，TOP 1-3 生成知识卡片。

## SQLite 去重表设计

```sql
CREATE TABLE paper_dedup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    doi TEXT,
    arxiv_id TEXT,
    url TEXT,
    title_hash TEXT NOT NULL,
    first_seen_date TEXT NOT NULL,
    last_seen_date TEXT NOT NULL,
    status TEXT DEFAULT 'candidate', -- candidate / card_generated / skipped / archived
    score REAL,
    notes TEXT
);
CREATE UNIQUE INDEX idx_doi ON paper_dedup(doi) WHERE doi IS NOT NULL;
CREATE UNIQUE INDEX idx_arxiv ON paper_dedup(arxiv_id) WHERE arxiv_id IS NOT NULL;
CREATE INDEX idx_title_hash ON paper_dedup(title_hash);
```

## 去重优先级

1. **DOI 匹配** — 最可靠
2. **arXiv ID 匹配** — arXiv 论文专用
3. **标题相似度** — 用标准化标题（去标点、小写、去空格）的 hash 对比
4. **URL 匹配** — 最后防线

## 日报模板

```markdown
# 论文阅读日报 — YYYY-MM-DD

## 搜索方向
{今日轮换方向} / {关键词}

## 候选论文 (TOP 10)
| # | 标题 | 来源 | 评分 | 相关度 | 是否精读 |
|---|------|------|------|--------|---------|
| 1 | ... | arXiv | 8.5 | GIS 0.9 | ✅ |
...

## 精选论文 (TOP 1-3)
### {标题}
{知识卡片核心部分}

## 统计
- 搜索到: N 篇
- 去重后新论文: N 篇
- 生成卡片: N 篇
- 入长期知识库: N 篇
```

## 每日限制

- 每日最多精读 3 篇
- 日报只输出 TOP 10 候选
- 评分 < 5 的不入日报（仅记录题录）
- 同一方向的论文如果重复度过高，只保留代表性论文

## 质量筛选集成

参见 `references/17_paper_quality_filter.md`：
- 候选论文 TOP 10 → 12 维评分卡快速初筛
- 进入精读 TOP 1-3 → 完整评分 + 最终分类

## 停损集成

参见 `references/18_stop_loss_rules.md`：
- 每日搜索论文不超过 30 分钟
- 每日精读不超过 3 篇
- 连续 3 篇读不懂 → 切换方向
