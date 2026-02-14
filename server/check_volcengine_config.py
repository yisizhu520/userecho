#!/usr/bin/env python3
"""火山引擎配置验证脚本

验证火山引擎是否正确配置，并测试截图识别功能

Usage:
    python check_volcengine_config.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(project_root / 'backend' / '.env')


def check_config() -> dict:
    """检查火山引擎配置"""
    print('='*60)
    print('🔍 检查火山引擎配置...')
    print('='*60)
    
    issues = []
    warnings = []
    
    # 1. 检查 API Key
    api_key = os.getenv('VOLCENGINE_API_KEY')
    if not api_key:
        issues.append('❌ VOLCENGINE_API_KEY 未配置')
    else:
        print(f'✅ VOLCENGINE_API_KEY: {api_key[:10]}...')
    
    # 2. 检查 Chat Endpoint
    chat_endpoint = os.getenv('VOLCENGINE_CHAT_ENDPOINT')
    if not chat_endpoint:
        issues.append('❌ VOLCENGINE_CHAT_ENDPOINT 未配置')
    else:
        print(f'✅ VOLCENGINE_CHAT_ENDPOINT: {chat_endpoint}')
    
    # 3. 检查 Vision Endpoint（可选）
    vision_endpoint = os.getenv('VOLCENGINE_VISION_ENDPOINT')
    if vision_endpoint:
        print(f'✅ VOLCENGINE_VISION_ENDPOINT: {vision_endpoint}')
        print('   (将优先使用此 Endpoint 进行图像识别)')
    else:
        warnings.append('⚠️  VOLCENGINE_VISION_ENDPOINT 未配置（将使用 CHAT_ENDPOINT）')
    
    # 4. 检查 Embedding Endpoint（可选）
    embedding_endpoint = os.getenv('VOLCENGINE_EMBEDDING_ENDPOINT')
    if embedding_endpoint:
        print(f'✅ VOLCENGINE_EMBEDDING_ENDPOINT: {embedding_endpoint}')
    else:
        warnings.append('⚠️  VOLCENGINE_EMBEDDING_ENDPOINT 未配置（将使用其他 Provider）')
    
    # 5. 检查默认 Provider
    default_provider = os.getenv('AI_DEFAULT_PROVIDER', 'deepseek')
    if default_provider == 'volcengine':
        print(f'✅ AI_DEFAULT_PROVIDER: {default_provider}')
    else:
        warnings.append(f'⚠️  AI_DEFAULT_PROVIDER 设置为 {default_provider}（不是 volcengine）')
    
    print('\n' + '='*60)
    
    # 输出警告
    if warnings:
        print('⚠️  警告：')
        for warning in warnings:
            print(f'  {warning}')
        print()
    
    # 输出错误
    if issues:
        print('❌ 配置错误：')
        for issue in issues:
            print(f'  {issue}')
        print()
        print('💡 请参考配置文档：')
        print('   docs/guides/ai-provider/volcengine-config-example.md')
        print('   docs/guides/ai-provider/volcengine-vision-setup.md')
        return {'success': False, 'issues': issues}
    
    if not warnings:
        print('✅ 所有配置正确！')
    
    return {'success': True}


async def test_screenshot_analysis():
    """测试截图识别功能"""
    print('\n' + '='*60)
    print('🧪 测试截图识别功能...')
    print('='*60)
    
    try:
        from backend.utils.ai_client import ai_client
        
        # 使用一个测试图片 URL（或本地图片）
        # 这里使用一个公开的示例图片
        test_image_url = 'https://via.placeholder.com/800x600.png?text=Test+Image'
        
        print(f'📸 测试图片: {test_image_url}')
        print('⏳ 调用 AI 识别...')
        
        result = await ai_client.analyze_screenshot(test_image_url)
        
        print('✅ 识别成功！')
        print(f'\n识别结果：')
        print(f'  平台: {result.get("platform", "未识别")}')
        print(f'  用户昵称: {result.get("user_name", "未识别")}')
        print(f'  反馈内容: {result.get("content", "未识别")[:50]}...')
        print(f'  反馈类型: {result.get("feedback_type", "未识别")}')
        print(f'  情感倾向: {result.get("sentiment", "未识别")}')
        print(f'  置信度: {result.get("confidence", 0):.2f}')
        
        return True
        
    except Exception as e:
        print(f'❌ 识别失败: {e}')
        print('\n可能的原因：')
        print('  1. API Key 或 Endpoint 不正确')
        print('  2. 网络连接问题')
        print('  3. 火山引擎服务异常')
        print('  4. Endpoint 对应的模型不支持图像识别')
        
        return False


def print_usage_guide():
    """打印使用指南"""
    print('\n' + '='*60)
    print('📖 后续步骤')
    print('='*60)
    print()
    print('1️⃣  确保配置正确后，重启服务：')
    print('   cd server')
    print('   source .venv/Scripts/activate')
    print('   uvicorn backend.main:app --reload')
    print()
    print('2️⃣  在产品中测试：')
    print('   - 登录 UserEcho')
    print('   - 进入"反馈管理" → "截图上传"')
    print('   - 上传一张微信/小红书截图')
    print('   - 查看 AI 识别结果')
    print()
    print('3️⃣  查看日志：')
    print('   tail -f backend/logs/server.log | grep screenshot')
    print()
    print('📚 参考文档：')
    print('   - docs/guides/ai-provider/volcengine-config-example.md')
    print('   - docs/guides/ai-provider/volcengine-vision-setup.md')
    print('   - docs/design/wechat-feedback-collect.md')
    print()


def main():
    """主函数"""
    # 1. 检查配置
    result = check_config()
    
    if not result['success']:
        print_usage_guide()
        sys.exit(1)
    
    # 2. 询问是否测试
    print()
    try:
        test_input = input('是否进行在线测试？(y/N): ').strip().lower()
        
        if test_input in ['y', 'yes']:
            import asyncio
            success = asyncio.run(test_screenshot_analysis())
            
            if not success:
                sys.exit(1)
        else:
            print('跳过在线测试')
    
    except KeyboardInterrupt:
        print('\n\n已取消')
        sys.exit(0)
    
    # 3. 打印使用指南
    print_usage_guide()


if __name__ == '__main__':
    main()
