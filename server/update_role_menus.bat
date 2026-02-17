@echo off
chcp 65001 >nul
echo ========================================
echo 更新角色菜单权限
echo ========================================
echo.

cd backend
call .venv\Scripts\activate.bat
python scripts/update_role_menus.py

pause
