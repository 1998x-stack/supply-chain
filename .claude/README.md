# Agent Skills 多平台发现路径

- Codex 官方自动发现位置是 .agents/skills/，这里为技能的唯一真实来源；.codex/skills/ 提供兼容的目录符号链接，但不要仅依赖该路径进行Codex自动发现。
- Claude Code 在 .claude/skills/ 使用指向 canonical 目录的相对符号链接，Claude支持symlinked skill folders。
- Pi 同时发现 .agents/skills 和 .pi/skills；后者符号链接可能在部分版本被去重或显示同名警告。若出现重复，优先保留 .agents/skills 发现入口。
- 技能均包含 SKILL.md、references/、scripts/、assets/，这些位于链接目标，避免维护四份容易失效的副本。
- Git 拉取请保留符号链接（Linux/macOS正常；Windows建议Git Bash+开发者模式或手动运行 tools/sync_skill_mirrors.py --copy）。
- 新技能须在 .agents/skills 下创建，并运行 python scripts/research_cli.py validate-skills。

