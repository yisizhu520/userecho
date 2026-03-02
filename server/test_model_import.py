"""测试模型导入和关系配置"""

import sys

print("=" * 60)
print("Step 1: Importing model module")
print("=" * 60)

try:
    from backend.app.userecho import model
    
    print(f"[OK] Model module imported")
    print(f"[OK] MergeSuggestion in model.__all__: {'MergeSuggestion' in model.__all__}")
    print(f"[OK] MergeSuggestion in dir(model): {'MergeSuggestion' in dir(model)}")
    
    print("\n" + "=" * 60)
    print("Step 2: Accessing Tenant class")
    print("=" * 60)
    
    tenant_cls = model.Tenant
    print(f"[OK] Tenant class: {tenant_cls}")
    print(f"[OK] Tenant.__tablename__: {tenant_cls.__tablename__}")
    
    print("\n" + "=" * 60)
    print("Step 3: Accessing MergeSuggestion class")
    print("=" * 60)
    
    merge_cls = model.MergeSuggestion
    print(f"[OK] MergeSuggestion class: {merge_cls}")
    print(f"[OK] MergeSuggestion.__tablename__: {merge_cls.__tablename__}")
    
    print("\n" + "=" * 60)
    print("Step 4: Checking relationship")
    print("=" * 60)
    
    # 触发 mapper 配置
    from sqlalchemy import inspect
    
    print("Configuring Tenant mapper...")
    tenant_mapper = inspect(tenant_cls)
    print(f"[OK] Tenant mapper: {tenant_mapper}")
    
    print("\nChecking merge_suggestions relationship...")
    if hasattr(tenant_mapper, 'relationships'):
        for key, rel in tenant_mapper.relationships.items():
            print(f"  - {key}: {rel}")
            if key == 'merge_suggestions':
                print(f"    Target: {rel.mapper.class_}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All models configured correctly")
    print("=" * 60)
    
except Exception as e:
    import traceback
    print("\n" + "=" * 60)
    print("[ERROR]")
    print("=" * 60)
    print(f"Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
