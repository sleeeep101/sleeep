# mcp_design_patterns_for_research — MCP 设计思想提炼

从 MCP 项目中提取的可用于学术研究的设计模式、方法论和流程模板。
全部只吸收思想，不接入 MCP server。

---

## 1. gdal-mcp — 空间分析前方法论验证

**来源**：`gdal-mcp` reflection middleware + `src/prompts/` (4 个 justification prompt)

### 核心思想

在执行关键 GIS/空间分析操作前，强制完成结构化方法论验证（Reflection Middleware）。不是"先做再改"，而是"先证明方法，再执行操作"。

### 验证框架

| 维度 | 内容 |
|---|---|
| **任务意图** | 这次空间分析要回答什么问题？ |
| **可选方法** | 至少列出 2-3 种可用的分析方法 |
| **选择理由** | 为什么选择这个方法而不是其他？（基于数据特征、研究目标、文献惯例） |
| **风险** | 这个方法在什么条件下可能失效？ |
| **置信度** | 对分析结果的信心（高/中/低）+ 依据 |
| **验证方式** | 如何验证分析结果的正确性？ |

### 适用场景

- CRS/投影选择 — 为什么用这个坐标系？
- 重采样方法选择 — 为什么用 bilinear 而不是 nearest/cubic？
- 空间查询范围 — 为什么选这个缓冲区半径/行政边界？
- 插值方法选择 — 为什么用 Kriging 而不是 IDW/Spline？
- 分类方法选择 — 为什么用 Random Forest 而不是 SVM/CNN？

### 缓存与复用

同一领域的 justification 可复用：
- 一次 CRS 选择证明 → 同一研究区域的所有分析共享
- 一次插值方法证明 → 同类数据可引用

### 与现有 academic-workflow 的关系

可强化 `18_stop_loss_rules.md`（防无限探索）和 `16_done_definition.md`（完成的定义）——在"开始分析"和"分析完成"两个节点加入方法论验证步骤。

---

## 2. second-brain-mcp — 知识压缩与笔记优先级

**来源**：`second-brain-mcp` vault_db.py (Ebbinghaus scoring) + vault_sleep.py (Vault Sleep 双轴压缩)

### 2.1 Ebbinghaus 笔记优先级评分

**公式**：`score = (access_count + 1) / ln(age_days + 1)`

| 参数 | 含义 |
|---|---|
| `access_count` | 该笔记被查看/引用的次数 |
| `age_days` | 距离最近一次修改的天数 |
| `+1` 项 | 防止除零和取对数异常 |

**设计直觉**：频繁访问的笔记得分高，随时间推移得分自然下降。与艾宾浩斯遗忘曲线一致——但不是强制遗忘，而是让"自然衰减"来决定优先级。

### 2.2 Vault Sleep 双轴压缩

按 `score × age` 自适应分级压缩旧笔记：

| 压缩等级 | 条件 | 压缩比例 | 方式 |
|---|---|---|---|
| text | score 高 + 近期 | 保持全文 | 不压缩 |
| large | score 中 + 较旧 | 压缩至 ~60% | 提取摘要和关键结论 |
| base | score 低 + 旧 | 压缩至 ~30% | 仅保留一句话总结 + 来源链接 |
| small | score 极低 + 很旧 | 压缩至 ~10% | 仅保留标题和核心关键词 |

**三级 fallback 链**：Gemini CLI（首选）→ Claude API（备用）→ 纯正则/规则匹配（保底）

### 2.3 长期知识库防膨胀思路

- **自动 wikilinks**：新笔记自动关联语义相似笔记，写入 frontmatter `related: [[...]]`
- **每周 Vault Sleep**：每周日自动压缩低活跃笔记
- **规则注入（不应用于 Claude 规则）**：高访问量笔记自动提取声明式约束，但**不用于 Claude 底层规则**（避免规则膨胀）

### 与现有 Personal-Brain 的关系

- `长期知识库.md` 可参考 Vault Sleep 的分级压缩策略，定期清理过时内容
- `lessons/` 月度经验库可参考 Ebbinghaus scoring 判断哪些经验需要保留
- 笔记优先级公式可用于 Daily Supervisor 的"知识库健康检查"

---

## 3. obsidian-mcp-sb — Markdown 知识库搜索权重与断点检测

**来源**：`obsidian-mcp-sb` 搜索权重设计 + knowledge gaps 检测 + spaced review 算法

### 3.1 搜索权重设计

当对 Personal-Brain 或 academic-workflow 的 Markdown 文件做全文搜索时，不同字段应赋予不同权重：

| 字段 | 权重 | 原因 |
|---|---|---|
| 标题 (h1/h2) | **3.0x** | 标题直接反映主题，最可靠 |
| 标签 (tags) | **2.5x** | 标签是用户主动标注，准确率高 |
| frontmatter (date/status/type) | **2.0x** | 结构化元数据 |
| 正文内容 | **1.0x** | 正文含大量噪音 |
| Wikilinks ([[...]])| **1.5x** | 跨文件引用信号 |

**应用**：当在 Personal-Brain 中用 grep/全文搜索时，优先匹配文件名（等价于标题权重）和 frontmatter。

### 3.2 Knowledge Gaps 检测

定期扫描 Personal-Brain 的 Markdown 文件，检测以下断点：

| 断点类型 | 检测方式 | 含义 |
|---|---|---|
| **孤儿链接** | `[[wikilink]]` 指向不存在的文件 | 打算写但还没写的笔记 |
| **未回答问题** | 以 `?` / `？` 结尾的行 | 尚未解决的研究问题 |
| **待补充标记** | `TODO` / `待补充` / `待确认` / `未确认` | 信息不完整的笔记 |
| **过期引用** | 链接指向已移动/删除的文件 | 需要更新的交叉引用 |

**应用**：可在 Daily Supervisor 中加入"Personal-Brain 知识断点检查"，每周输出一次断裂链接和未解决问题清单。

### 3.3 Spaced Review 间隔复习

基于入站链接重要性排名的间隔复习算法：
- 被引用最多的笔记 → 复习优先级最高
- 长期未被引用的笔记 → 降级或归档

**公式**：`review_priority = inbound_links × (1 / ln(age_days + 1))`

**应用**：Personal-Brain 的 maintenance/ 目录文件可定期按此算法排序，优先 review 高频引用的核心文件。

---

## 4. zotmcp — 文献综述 4 阶段流程

**来源**：`zotmcp` main.py literature_review prompt + README 搜索质量 caveats

### 4.1 文献综述 4 阶段

```
Phase 1: SEARCH      → 多源检索，优先查 Zotero 已有库，再查外部
Phase 2: EVALUATE    → 按来源评估标准逐篇筛选
Phase 3: SYNTHESIZE  → 整合核心发现、方法对比、研究空白
Phase 4: QUALITY CHECK → 自检清单 + 引用完整性验证
```

### 4.2 来源评估标准

| 标准 | 权重 | 说明 |
|---|---|---|
| **Recency（时效性）** | 高 | 优先 2024-2026 年发表 |
| **Authority（权威性）** | 中 | 高引论文、知名期刊/会议 |
| **Relevance（相关性）** | 最高 | 必须与 GIS/遥感/空间分析直接相关 |
| **Methodology（方法质量）** | 中 | 方法描述是否清晰可复现 |
| **Accessibility（可获取性）** | 必要条件 | 必须能读到全文 |

### 4.3 搜索质量 caveats（实测经验）

| 问题 | 现象 | 对策 |
|---|---|---|
| Embedding 同义词 | "DEM" 和 "digital elevation model" 在向量搜索中可能不匹配 | 同时使用关键词搜索和语义搜索（hybrid mode） |
| 分数阈值 | 语义搜索的相似度分数在不同查询间不可比 | 不要在跨查询比较中使用绝对分数，用相对排名 |
| 混合模式优势 | 纯向量搜索可能遗漏精确关键词匹配 | hybrid = BM25 + vector + fuzzy，优先用混合模式 |
| 标题 vs 摘要 vs 全文 | 仅搜标题遗漏重要论文，仅搜全文字段噪音大 | 优先标题+摘要组合搜索，必要时扩展到全文 |

### 4.4 严格约束

- 不得使用模型通用知识替代论文内容
- 不得编造引用
- 不确定的 DOI → 标注"DOI：未确认"
- 仅基于摘要的判断 → 标注"仅基于摘要"
- 每篇引用的论文必须能在 Zotero 或 arXiv 中找到

### 与现有 academic-workflow 的关系

可补充到 `02_research_pipeline.md`（研究流程）和 `08_review_checklists.md`（审查清单）中，作为文献综述的质量标准。
