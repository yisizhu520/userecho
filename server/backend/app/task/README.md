## 任务介绍

当前任务使用 Celery
实现，实施方案请查看 [#225](https://github.com/fastapi-practices/fastapi_best_architecture/discussions/225)

## 定时任务

在 `backend/app/task/tasks/beat.py` 文件内编写相关定时任务

### 简单任务

在 `backend/app/task/tasks/tasks.py` 文件内编写相关任务代码

### 层级任务

如果你想对任务进行目录层级划分，使任务结构更加清晰，你可以新建任意目录，但必须注意的是

1. 在 `backend/app/task/tasks` 目录下新建 python 包目录
2. 在新建目录下，务必添加 `tasks.py` 文件，并在此文件中编写相关任务代码

## 消息代理

当前项目使用 **Redis** 作为 Celery 消息代理。

- 本地开发: 使用 Redis (database 1)
- 生产环境: 使用 Redis (database 1)

> **注意**: 项目已移除 RabbitMQ 支持，简化部署架构。
