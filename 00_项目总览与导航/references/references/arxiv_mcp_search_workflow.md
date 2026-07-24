# arxiv_mcp_search_workflow — arXiv MCP 即时搜索工作流

固化从 Claude 直接搜索 arXiv 的即时检索规则，与每日论文阅读定时脚本互补。

## 与每日论文阅读脚本的分工

| 场景 | 工具 | 说明 |
|---|---|---|
| 每日定时批量搜索（8方向×4关键词） | `daily_paper_curator.py`（定时 12:00） | 自动评分、去重、生成日报和知识卡片 |
| 研究过程中即时检索 | mcp-simple-arxiv（交互式 MCP） | Claude 对话中直接搜索，即时返回 |
| 按方向深度检索 | mcp-simple-arxiv | 针对单一方向的精确组合搜索 |
| 批量论文知识卡片生成 | `daily_paper_curator.py` | 脚本自动生成 20 字段知识卡片 |
| 搜索结果转知识卡片 | mcp-simple-arxiv + Claude 手动 | 交互式选择搜索结果中的论文生成卡片 |

**核心原则**：定时脚本负责"广撒网"，MCP 负责"精准捕捞"。不相互替代。

---

## 使用 mcp-simple-arxiv 的场景

1. 论文写作时需要快速验证某个方向是否有最新论文
2. GIS/遥感方法迁移时需要查特定方法的论文
3. 文献综述时需要针对特定关键词做深度检索
4. 需要按作者、分类、日期精确过滤的检索
5. 每日脚本错过了一篇重要论文，需要手动补充

## 仍使用每日论文阅读脚本的场景

1. 每天早上 12:00 的定时全面搜索
2. 自动评分、去重、日报生成
3. 自动生成 20 字段知识卡片
4. 自动附加到长期知识库
5. 周总结和月度 lessons 的数据来源

---

## arXiv 搜索策略（源自 mcp-simple-arxiv）

### 搜索精确度排序

```
1. ti:"精确词组" AND cat:分类码     ← 最精确，首选
2. ti:"关键词" AND au:作者          ← 标题+作者
3. cat:分类码 AND ti:关键词          ← 分类+标题
4. ti:"关键词"                      ← 仅标题
5. "关键词"                         ← 全字段（宽泛，少用）
```

### 字段前缀

| 前缀 | 含义 | 示例 |
|---|---|---|
| `ti:` | 标题 | `ti:"digital elevation model"` |
| `abs:` | 摘要 | `abs:"landslide susceptibility"` |
| `au:` | 作者 | `au:Hengl` |
| `cat:` | 分类 | `cat:cs.CV`（计算机视觉）、`cat:physics.geo-ph`（地球物理） |

### 运算符

- `AND` — 且
- `OR` — 或
- `ANDNOT` — 排除

### 日期过滤

```
date_from="2025-01-01"                   # 2025年以后
date_from="2024-01-01", date_to="2024-12-31"  # 仅2024年
date_to="2020-12-31"                     # 2020年以前
```

### 排序方式

| sort_by | 含义 | 适用场景 |
|---|---|---|
| `submitted_date` | 按投稿日期 | 最新论文（默认） |
| `updated_date` | 按更新日期 | 最近修订版 |
| `relevance` | 按相关性 | 精确搜索 |

### 常见错误

- ❌ 裸关键词如 `machine learning` — arXiv 默认 OR 逻辑，返回大量无关结果
- ❌ 不先用 `list_categories` 查分类码就直接搜
- ❌ 搜索词太宽泛不限制时间范围
- ✅ 先用 `ti:` + `cat:` 精确组合
- ✅ 先查分类 → 再搜索
- ✅ 限制 `max_results=10`，不够再扩充

---

## 8 方向搜索关键词模板

以下组合用于 mcp-simple-arxiv 即时搜索，与定时脚本的 8 方向×4 关键词互补。

### 1. DEM 与地形分析

```text
ti:"digital elevation model" AND (ti:erosion OR ti:terrain OR ti:geomorphology)
cat:physics.geo-ph AND ti:"DEM" AND date_from="2024-01-01"
ti:"landslide susceptibility" AND (ti:machine learning OR ti:deep learning)
```

### 2. GIS 空间建模

```text
ti:"spatial analysis" AND (ti:Python OR ti:geospatial) AND date_from="2024-01-01"
ti:"WebGIS" OR ti:"geospatial AI" AND cat:cs.CY
ti:"spatial data science" AND date_from="2025-01-01"
```

### 3. 遥感与土地利用

```text
ti:"land use" AND ti:"remote sensing" AND ti:"deep learning"
ti:"sentinel" AND ti:"land cover" AND date_from="2024-01-01"
ti:"GEE" OR ti:"Google Earth Engine" AND ti:"classification"
ti:"hyperspectral" AND ti:"deep learning" AND date_from="2024-01-01"
```

### 4. 机器学习迁移

```text
ti:"causal inference" AND ti:spatial AND date_from="2024-01-01"
ti:"time series" AND ti:"remote sensing" AND ti:transformer
ti:"transfer learning" AND (ti:"remote sensing" OR ti:geospatial)
```

### 5. 生态与自然资源

```text
ti:"ecosystem service" AND ti:GIS
ti:"soil erosion" AND ti:modeling
ti:"watershed" AND ti:analysis AND ti:GIS
```

### 6. 实验设计与方法

```text
ti:"indicator system" AND ti:GIS
ti:"quantitative methodology" AND ti:geospatial
ti:"uncertainty quantification" AND ti:"spatial analysis"
```

### 7. AI 与编程工具

```text
ti:"AI agent" AND (ti:coding OR ti:programming) AND date_from="2025-01-01"
ti:"LLM" AND ti:scientific AND ti:research AND date_from="2025-01-01"
ti:"Python" AND ti:"geospatial" AND ti:pipeline
```

### 8. 社会与交叉学科

```text
ti:"urban heat island" AND ti:GIS
ti:"climate adaptation" AND ti:spatial
ti:"environmental justice" AND ti:"spatial analysis"
```

---

## 搜索结果筛选规则

搜索结果按以下标准筛选（引用 `17_paper_quality_filter.md`）：

1. 标题与 GIS/遥感/空间分析相关 → 保留
2. 有 DOI 或 arXiv ID → 优先
3. 2024-2026 年发表 → 优先
4. 开源/可获取全文 → 优先
5. 方法可迁移到 GIS → 标记高分
6. 纯计算机科学/纯数学/纯物理 → 降级或舍弃

---

## 搜索结果转论文知识卡片

搜索结果中选中的论文，按 `04_paper_card_template.md` 的 20 字段格式生成知识卡片：

标题 / 作者 / 年份 / 来源 / DOI / 全文链接 / 是否免费 /
一句话总结 / 研究问题 / 数据来源 / 方法流程 / 核心方法 / 创新点 /
主要结果 / 局限 / 可迁移GIS的点 / 可迁移个人项目的点 /
可转AI Code任务 / 写作学习卡片 / 价值评分

---

## 搜索结果进入长期知识库

mcp-simple-arxiv 搜索到的论文，如果被选中生成知识卡片，按以下路径沉淀：

1. 知识卡片 → `长期知识库.md`（DOI 去重，标记日期）
2. 可迁移方法 → 方法迁移库（周总结时整理）
3. 写作句式 → 写作素材库（步骤 8 提取）
4. AI Code 任务 → AI Code 任务池（步骤 7 整理）

---

## 隔离试用计划

`mcp-simple-arxiv` 的 MCP server 在后续单独任务中隔离试用：

1. 单独建测试目录
2. 不影响现有 academic-workflow
3. 不修改 Claude 正式配置
4. `pip install mcp-simple-arxiv`（记录但用户确认后再执行）
5. 测试 3 个方向：GIS/遥感、DEM/地貌水文、空间分析/空间统计
6. 测试输出是否能转成论文知识卡片
7. 测试完写入试用报告到 `Personal-Brain\reports\`
