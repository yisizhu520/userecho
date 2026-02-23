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
        reload=True,
        reload_dirs=["backend"],  # Only watch backend directory
        reload_excludes=["**/__pycache__/**", "**/.pytest_cache/**"],
    )

    elapsed = time.time() - start_time
    print(f"\n{'=' * 80}", flush=True)
    print(f"[Startup] Service started! Total time: {elapsed:.2f}s", flush=True)
    print(f"{'=' * 80}\n", flush=True)
