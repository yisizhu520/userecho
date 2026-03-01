import socketio

from backend.common.socketio.utils import get_redis_manager_kwargs

# 全局单例，懒加载
_sio_emitter: socketio.AsyncServer | None = None


async def get_sio_emitter() -> socketio.AsyncServer:
    """
    获取 Socket.IO Emitter 实例（懒加载）

    用于解决 Celery Worker 中 Loop 不匹配的问题：
    - 全局 sio 实例是在模块导入时创建的，绑定到了当时（或无）Loop。
    - Celery 运行时有自己的 Loop，直接使用全局 sio 会导致 Future attached to a different loop 错误。
    - 这里确保 AsyncServer 和 AsyncRedisManager 在当前运行的 Loop 中创建。
    """
    global _sio_emitter
    if _sio_emitter is None:
        _sio_emitter = socketio.AsyncServer(
            client_manager=socketio.AsyncRedisManager(**get_redis_manager_kwargs()),
            async_mode="asgi",
            # 与 server.py 保持一致的命名空间配置，尽管 emit 默认不需要
            namespaces=["/ws"],
        )
    return _sio_emitter


async def task_notification(msg: str) -> None:
    """
    任务通知

    :param msg: 通知信息
    :return:
    """
    sio = await get_sio_emitter()
    # 默认发送到所有 Namespace，但通常客户端连接在 /ws
    # 显式指定 namespace="/ws" 以确保连接在 /ws 的客户端能收到
    await sio.emit("task_notification", {"msg": msg}, namespace="/ws")
