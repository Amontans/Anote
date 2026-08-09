# Anote 插件目录

插件 = 独立的 Python 脚本（薄适配器，遵循 docs/CODING.md）：
- `anote plugin list`        列出已装插件
- `anote plugin add <脚本>`  安装（复制到本目录）
- `anote plugin run <名> [参数]`  运行

插件访问能力：`from anote.core import Config, Result`；`from anote.services import ...`
（src/ 已在运行路径中）。示例见 example_plugin.py。
