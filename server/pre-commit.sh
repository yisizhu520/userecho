#!/usr/bin/env bash
cd "$(dirname "$0")"

# 使用 uv run 运行 pre-commit，确保依赖环境正确
uv run pre-commit run --all-files --verbose --show-diff-on-failure
