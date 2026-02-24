"""通用的环境变量设置代码片段（用于所有初始化脚本）"""

# 在所有初始化脚本的开头（import 任何 backend 模块之前）添加以下代码：

import os
from pathlib import Path

# 【重要】确保使用 .env.demo 配置文件（必须在导入 backend 模块之前设置）
if "ENV_FILE" not in os.environ:
    # 尝试查找 .env.demo 文件
    script_path = Path(__file__).resolve()
    backend_path = script_path.parent.parent
    
    # 优先使用 backend/.env.demo
    env_demo_path = backend_path / ".env.demo"
    if env_demo_path.exists():
        os.environ["ENV_FILE"] = str(env_demo_path)
        print(f"✅ 使用配置文件: {env_demo_path}")
    else:
        # 尝试 server/.env.demo
        env_demo_path = backend_path.parent / ".env.demo"
        if env_demo_path.exists():
            os.environ["ENV_FILE"] = str(env_demo_path)
            print(f"✅ 使用配置文件: {env_demo_path}")
        else:
            print(f"⚠️  未找到 .env.demo，使用默认配置")
