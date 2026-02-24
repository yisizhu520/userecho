import os
import sys
import time

import uvicorn

if __name__ == "__main__":
    # 为什么独立此启动文件：https://stackoverflow.com/questions/64003384

    # DEBUG:
    # 如果你喜欢在 IDE 中进行 DEBUG，可在 IDE 中直接右键启动此文件
    # 如果你喜欢通过 print 方式进行调试，建议使用 fba cli 方式启动服务

    # Warning:
    # 如果你正在通过 python 命令启动此文件，请遵循以下事宜：
    # 1. 按照官方文档通过 uv 安装依赖
    # 2. 命令行空间位于 backend 目录下

    # 确保 ENV_FILE 环境变量被正确设置（支持 Demo 模式启动）
    # 从命令行参数或环境变量读取
    env_file = os.getenv("ENV_FILE")
    if len(sys.argv) > 1 and sys.argv[1].startswith("--env="):
        env_file = sys.argv[1].split("=", 1)[1]
        os.environ["ENV_FILE"] = env_file

    if env_file:
        print(f"[Config] Using environment file: {env_file}", flush=True)
        # 确保环境变量在子进程中也生效
        if "ENV_FILE" not in os.environ:
            os.environ["ENV_FILE"] = env_file
    else:
        print("[Config] Using default environment file: .env", flush=True)

    start_time = time.time()
    print(f"\n{'=' * 80}", flush=True)
    print(f"[Startup] Service starting... Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"{'=' * 80}\n", flush=True)

    # Fix: Limit reload watching to server directory only
    # Problem: Uvicorn was scanning 98K+ files including front/node_modules
    # Solution: Use reload_dirs to only watch server/backend
    uvicorn.run(
        app="backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,  # Disable hot reload
        reload_dirs=["backend"],  # Only watch backend directory
        reload_excludes=["**/__pycache__/**", "**/.pytest_cache/**"],
    )

    elapsed = time.time() - start_time
    print(f"\n{'=' * 80}", flush=True)
    print(f"[Startup] Service started! Total time: {elapsed:.2f}s", flush=True)
    print(f"{'=' * 80}\n", flush=True)
