# 为 ARIS-Movie-Director 做贡献

🌐 **中文** · [English](CONTRIBUTING.md)

感谢出手。本仓库的核心论点是:**一个生成出来的视觉故事应当是可审计的** —— 所以这里唯一最重要的规则是:**永远别让任何一道 gate 失去牙齿。** 一个让"错误的 / 没有出处的"帧更容易被发布的改动,就是退步 —— 哪怕所有测试照样通过。拿不准时,fail closed(失败时拒绝放行)。

新来的?先读 [README](README_CN.md)(两条流水线是什么),再看这份。你**绝不能削弱**的那些确定性保证,活在 `cli/validate_wiki.py`、`skills/comic-director/scripts/run_comic.py`、`packages/core/spiral_engine.js`,以及 `skills/method-figure/scripts/{compile_brief,content_diff,validate_blueprint}.py` 里。

## 开发环境

```bash
python3 -m pip install -r requirements.txt   # jsonschema(其余都是标准库)
# Node ≥ 18,用于 `node --check packages/core/spiral_engine.js`
```

外部工具(`codex`、`gemini`、无头 `chrome`/`chromium`)只在**计费**阶段(图像烤制、跨模型评审、SVG 栅格化)才需要 —— 给确定性 gate 做贡献**不需要**它们。用 `python3 cli/preflight.py` 检查你的环境。

## 绿灯检查 —— 每次 PR 前都跑

```bash
bash tests/smoke.sh
```

这正是 CI 跑的东西(`.github/workflows/ci.yml`)。它**只**演练那些不花信用、不需要 Chrome、不联网的 gate:`py_compile` + `node --check`、对两个示例跑 `validate_wiki`、`run_comic.py --dry-run`、`compile_brief` Step-0、`validate_blueprint`,以及 `tests/test_gates.py` 里的回归套件。一个 PR 必须让它保持绿。计费阶段被刻意排除在 CI 之外(它们需要凭据 + 浏览器)。

## 可以贡献什么

| 领域 | 在哪 | 备注 |
|---|---|---|
| **作者类 skill(SOP)** | `skills/comic-*`、`skills/method-figure` | 它们是供 coding agent *跟随*的流程 —— 散文本身就是产物。保持链接可解析。 |
| **确定性引擎 / gate** | `cli/`、`packages/core/`、`skills/*/scripts/` | 牙齿所在。见下方硬规则。 |
| **示例项目** | `examples/<name>/` | 必须通过 `validate_wiki`。 |
| **Schema** | `schemas/`、`skills/method-figure/schemas/` | 与 enforcer 保持同步(下方有漂移守卫)。 |
| **文档** | `README.md`、`docs/`、skill 的 `references/` | 见下方诚实规则。 |

## 引擎 / gate 改动的硬规则

1. **两个 comic 引擎要保持同步。** `packages/core/spiral_engine.js` 是**规范(canonical)**引擎;`skills/comic-director/scripts/run_comic.py` 是它的逐行移植。对一个的修复**必须**也落到另一个上(JS 引擎是通过一个 `agent()` prompt 来写 wiki 的,所以它的"修复"就是把完整的 schema 骨架写进 prompt)。这里真实反复出现过的 bug 就是"只修了 Python 移植版"。
2. **没有一个证明新行为的测试,就别削弱任何 fail-closed 检查。** `content_diff.py` 里的每一个否决、panel gate 里的 literal-diff 精确性、`compile_brief` 的可追溯性、以及 `cfg_usable`/`p0_proof` 的预检 —— 都是承重的。你改了其中之一,就在 `tests/test_gates.py` 里加 / 调一个用例,把期望的行为锁住。
3. **没有任何模型能自证通过。** 一个烤出的 artifact,由一个**不同模型家族** + 一次确定性 diff 来评判,绝不由做出它的那个模型来评判。如果你的改动涉及正确性,在声称它没问题之前先做一次跨模型评审(例如让一个非 Claude 模型读那份 diff)。见 `protocols/acceptance-gate.md`。
4. **Schema ↔ enforcer 要步调一致。** `validate_wiki.py` 有一个漂移守卫:`schemas/node_schema.json` 里每个 `node_type` 都必须有一个对应的 `PAYLOAD_REQUIRED` 条目,反之亦然。两边一起改。
5. **文档与主张要诚实。** 这个项目对措辞很挑:
   - 说"对照**撰写出的** `expected_literals` 做核对" —— *不是*"对世界做了事实核查"(`comic.json` 里一个错的事实会被忠实复现;gate 验证的是对真值源的忠实度,而非真理本身)。
   - 那份 trace 是**可审阅(inspectable)**的,而非逐字节"可复现(reproducible)"的(图像生成并非确定性)。
   - 框架常量文本(例如蓝图的 `rail`)用 `framework:*` 来源标记,而不是 `brief:*`。
   - 不要主张这个领域已经有了的"新颖性"(见 README 的"相关工作"一节)。
   - `--strict-author-gates` 是一个**可选的生产检查**,不是默认项:`validate_wiki.py` 默认允许裸锁定的作者
     节点用于开发/实验(CI 断言不带该旗标 fixture 也通过,见 `tests/test_gates.py`)。要提交到 release/评审的
     项目**应当**在自己的清单里运行 `validate_wiki.py --strict-author-gates`,并用 `decides`/`reviews` 边为
     每个作者锁定建立门控 —— 但不要声称默认的 smoke/CI 会强制它(它不会)。

## 加一个示例项目

一个项目通过 `examples/<name>/movie.project.json` + 一份 `comic.json` IR + 一份 `wiki/` trace 接入。最小可复制的样板是 [`examples/comic_min_author/`](examples/comic_min_author/)(每种作者节点类型各一个合法节点)。开 PR 之前:

```bash
python3 cli/validate_wiki.py examples/<name>                 # 必须 PASS
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <P> --panels <S..> --dry-run
```

**不要**提交生成出来的产物(`wiki/` 下 `build_prompt.py` 的输出 —— `log.md`、`prompt_build/`、生成的 `prompt_*` 节点 —— 都是可再生的;别让它们进 diff)。

## PR 自查清单

- [ ] `bash tests/smoke.sh` 是绿的。
- [ ] 动了 gate/引擎?两个 comic 引擎都更新了,**并且** `tests/test_gates.py` 有一个用例覆盖它。
- [ ] 动了 schema?enforcer(`validate_wiki.py` 的 `PAYLOAD_REQUIRED` / `EDGE_TYPES`)同步更新到匹配。
- [ ] 没有新的文档 over-claim;措辞遵守诚实规则。
- [ ] 链接可解析;没有把生成/临时文件加进暂存。
- [ ] **没有任何 secret、没有任何绝对家目录路径**(`/Users/...`、`/home/...`)出现在 diff 里 —— 本仓库是**公开**的。`validate_wiki` 会扫 wiki payload 里的这类内容;脚本/文档也请再核一遍。

## 提交与 PR

- 约定式前缀:`fix(gates):`、`feat(skill):`、`docs(readme):`、`ci:`、`test:`。
- PR 保持聚焦;说明一个 gate 改动**保住或加强了哪条保证**。
- 评审里友善而具体。标准是正确 + 诚实,而非数量。

## Issue 与安全

- Bug / 想法 → 开一个带复现步骤的 GitHub issue(一行能让 `bash tests/smoke.sh` 失败的命令最理想)。
- 找到了一条让"错误的 / 没有出处的"artifact 能通过某道 gate 的路子?那是价值最高的报告 —— 请把它标出来(愿意的话可以私下),而不是开一个公开的、像漏洞利用示范那样的 issue。

参与贡献即表示你同意:你的工作以本仓库的 [MIT 许可证](LICENSE) 授权。
