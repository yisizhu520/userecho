#!/usr/bin/env python
"""Wrapper script to import demo data with proper error handling"""

import os
import sys
from pathlib import Path

# 设置环境变量，使用本地 .env 文件
backend_path = Path(__file__).resolve().parent / "backend"
env_file = backend_path / ".env"
if env_file.exists():
    os.environ["ENV_FILE"] = str(env_file)
    print(f"✅ Using ENV_FILE: {env_file}")
else:
    print(f"❌ .env file not found: {env_file}")
    sys.exit(1)

# 添加 backend 到 Python 路径
sys.path.insert(0, str(backend_path))

# 直接导入并运行
try:
    from scripts.init_demo_data import main
    import asyncio

    # 运行初始化（带 reset 参数）
    asyncio.run(main(reset=True))
    print("\n🎉 数据导入完成！")
except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
