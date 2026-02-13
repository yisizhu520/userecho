"""修复所有 userecho 模型的 init=False 问题"""
import re
from pathlib import Path

models_dir = Path("app/userecho/model")

# 需要修复的文件
files_to_fix = [
    "customer.py", 
    "topic.py", 
    "priority_score.py", 
    "status_history.py", 
    "manual_adjustment.py",
    "tenant.py"
]

for filename in files_to_fix:
    filepath = models_dir / filename
    if not filepath.exists():
        print(f"⚠️  {filename} 不存在")
        continue
    
    content = filepath.read_text(encoding='utf-8')
    
    # 移除重复的 init=False,
    content = re.sub(r'init=False,\s*', '', content)
    
    # 在 mapped_column 的结尾添加 init=False (在最后一个参数后)
    # 匹配模式: mapped_column(..., comment='xxx')
    # 替换为: mapped_column(..., comment='xxx', init=False)
    content = re.sub(
        r"(mapped_column\([^)]*comment=\s*['\"][^'\"]*['\"])\s*\)",
        r"\1, init=False)",
        content
    )
    
    filepath.write_text(content, encoding='utf-8')
    print(f"✅ 修复完成: {filename}")

print("\n🎉 所有文件修复完成！")
