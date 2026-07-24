# 方法与代码库

本板块把论文中已核验、可迁移的方法转化为可复现的地理研究项目，而不是存放一次性脚本或未验证的结论。

## 使用顺序

1. 在 `方法库索引.md` 中确认方法已有全文级或人工精读证据。
2. 为一个具体研究建立独立项目目录，并按 `地理研究项目模板.md` 建立数据、代码、配置、测试和输出边界。
3. 在提交、分享或交接前运行：

   ```powershell
   python project_quality_gate.py --project "你的项目目录"
   ```

4. 只将文档、可执行代码、配置模板和小型合成示例纳入公开版本；原始数据、处理结果、日志、缓存、账户配置与个人路径必须留在项目外或被忽略。

## 质量门

一个可交接项目至少应具备：

- 明确的问题、方法、输入、输出与适用范围；
- `README.md`、许可证说明和可复现环境声明；
- 可运行脚本与最小测试；
- 数据分层和 `.gitignore` 边界；
- 能从干净环境复现一项主结果或明确说明不能复现的原因。

## 来源与适配

2026-07-24 融合 [Cookiecutter Data Science](https://github.com/drivendataorg/cookiecutter-data-science)（MIT）的项目分层思想，以及 [RE-paper-writing](https://github.com/Research-Equality/RE-paper-writing)（MIT）的证据、复现与投稿 QA 原则。这里仅提炼规则与自编质量门，不复制外部项目代码。
