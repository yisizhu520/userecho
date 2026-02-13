#!/bin/bash
echo "========================================"
echo "初始化业务菜单和角色"
echo "========================================"
echo

cd backend || exit
source .venv/bin/activate
python scripts/init_business_menus.py

