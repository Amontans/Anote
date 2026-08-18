#!/usr/bin/env python3
"""anote external —— 外部 MCP server 接入（薄适配器；逻辑在 services/mcp_client.py）。

用法:
  anote external list                        # 列出注册的外部 server
  anote external call <名> <工具> [--args '{"k":"v"}']
接口声明（契约）:
    输入: 见上；配置在 <数据根>/.anote/external.json
    输出: stdout=结果；退出码 0/1
    副作用: 无（只调外部服务；注册表在 <数据根>/.anote/external.json）
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.services.mcp_client import call_server, load_servers  # noqa: E402


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] == "list":
        servers = load_servers()
        if not servers:
            print("（未注册外部 server。配置 <数据根>/.anote/external.json:）")
            print("  路径: <数据根>/.anote/external.json")
            print('  {"servers": {"名": {"command": ["python3", "-m", "xxx"]}}}')
            return 0
        for name, cfg in servers.items():
            print(f"  • {name}  command={' '.join(cfg.get('command', []))}")
        return 0
    if args[0] == "call" and len(args) >= 3:
        name, tool = args[1], args[2]
        call_args = None
        if "--args" in args:
            i = args.index("--args")
            if i + 1 < len(args):
                try:
                    call_args = json.loads(args[i + 1])
                except Exception:  # noqa: BLE001
                    print("✗ --args 需为 JSON")
                    return 1
        print(call_server(name, tool, call_args))
        return 0
    print("用法: anote external {list|call <名> <工具> [--args JSON]}")
    return 0


if __name__ == "__main__":
    sys.exit(__import__("anote.cli", fromlist=["run"]).run(main))
