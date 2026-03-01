"""批量任务处理器注册

此模块用于导入所有处理器，确保它们在应用启动时被注册。
"""

# 导入所有处理器，触发 @batch_task_handler 装饰器
from backend.app.batch.handler import screenshot_recognition  # noqa: F401

# 你可以在这里导入更多处理器
# from backend.app.batch.handler import excel_import  # noqa: F401
# from backend.app.batch.handler import data_export  # noqa: F401
