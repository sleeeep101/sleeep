# 六维论文评分系统

> 来源：nature-literature-pipeline `references/scoring-system.md`
> 改编：融入 academic-workflow 7维100分制 + 导师方向匹配

## 原始 6 维（nature-literature-pipeline）

用于粗筛阶段（30→5篇）。每篇 0-100 分，6 个维度加权。

| # | 维度 | 权重 | 测量内容 |
|---|------|:---:|----------|
| 1 | Topic Match | 35 | 与核心研究问题的匹配度 |
| 2 | Methodological Value | 20 | 方法质量和适用性 |
| 3 | Journal/Source Quality | 15 | 期刊声望、引用影响、可信度 |
| 4 | Research Network Relevance | 10 | 与被追踪作者/机构的关联 |
| 5 | Applied/Engineering Value | 10 | 实用价值：协议、数据集、基准、工程洞察 |
| 6 | Archival Value | 10 | 长期参考价值：综述潜力、基础地位、教学用途 |

### 门控规则

- 维度 1（Topic Match）< 10 分 → 自动拒绝，无论其他分数如何
- 声望期刊的论文可能在维度 3 得分高但维度 1 低 → 门控规则阻止此类误纳

### 校准

运行 2-3 轮后检查分数分布：
- Top 论文持续 90+ → 评分过松
- 无论文超过 60 → 关键词可能过窄或领域稀疏
- 根据反馈调整权重

## 与 academic-workflow 7维100分制的对照

| nature-skills 6维 | academic-workflow 7维 | 映射关系 |
|-------------------|----------------------|----------|
| Topic Match (35) | 导师方向相关度 (20) + GIS/遥感迁移价值 (15) | 拆分+重新加权 |
| Methodological Value (20) | 方法流程完整度 (20) | 1:1 对应 |
| Journal Quality (15) | 年份时效性 (10) + 结果可信度 (15) 部分 | 需要重新组合 |
| Network Relevance (10) | — | academic-workflow 无此维度（用户不追踪特定作者） |
| Applied Value (10) | GIS/遥感迁移价值 (15) + 对选题/作品集帮助 (5) | 合并 |
| Archival Value (10) | 对选题/作品集帮助 (5) 部分 | 部分覆盖 |
| — | 数据与研究区清晰度 (15) | academic-workflow 独有 |

## 推荐使用策略

**日常桌面PDF处理流程**：继续使用 academic-workflow 的 A/B/C/X 四级预筛（`04_paper_prescreen_filter.md`）+ 7维100分制。

**若未来恢复在线检索**：可参考 nature-literature-pipeline 的 6 维评分作为检索阶段的粗筛，再进入 A/B/C/X 精筛。

**关键差异**：nature-skills 的 6 维是为**在线检索粗筛**设计的（30→5，快节奏）；academic-workflow 的 7 维是为**精读后入库评分**设计的（全量精读后可深入评估）。两者定位不同，不互相替代。
