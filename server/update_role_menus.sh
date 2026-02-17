#!/bin/bash
echo "========================================"
echo "更新角色菜单权限"
echo "========================================"
echo

cd backend || exit
source .venv/Scripts/activate
python scripts/update_role_menus.py
