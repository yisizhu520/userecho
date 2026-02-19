# Celery（数据库结果后端）常见问题：`task_id_sequence` 不存在

## 现象

执行 Celery 任务时，worker 日志出现类似错误：

```
psycopg.errors.UndefinedTable: relation "task_id_sequence" does not exist
... VALUES (nextval('task_id_sequence'), ...)
```

## 根因

本项目使用 Postgres 的自增主键（`SERIAL/IDENTITY`）来生成 `task_result.id`。

但如果 ORM 模型显式绑定了 `Sequence('task_id_sequence')`，SQLAlchemy 会在插入时强制生成 `nextval('task_id_sequence')`。
而 Alembic 迁移并不会创建名为 `task_id_sequence` 的序列，于是就会报上述错误。

## 解决方案

1. 更新代码到最新版本（已移除对 `task_id_sequence` 的显式依赖）。
2. 确保数据库已执行过迁移，存在 `task_result` / `task_set_result` 表。

   在 `server/backend` 目录执行：

   ```bash
   alembic upgrade head
   ```

3. 重启 Celery worker/beat。

## 如何确认已生效

修复后，插入 `task_result` 时不应再出现 `nextval('task_id_sequence')`。
如果你仍然看到该 SQL 片段，说明 worker 还在跑旧代码（或旧镜像没有更新）。
