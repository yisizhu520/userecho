@echo off
chcp 65001 >nul
echo ========================================
echo 初始化业务菜单和角色
echo ========================================
echo.

cd backend
call .venv\Scripts\activate.bat
python scripts/init_business_menus.py

pause

