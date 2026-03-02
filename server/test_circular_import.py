"""测试循环导入"""

print("Test 1: Import MergeSuggestion")
from backend.app.userecho.model.merge_suggestion import MergeSuggestion

print(f"  OK: {MergeSuggestion}")

print("\nTest 2: Import Tenant")
from backend.app.userecho.model.tenant import Tenant

print(f"  OK: {Tenant}")

print("\nTest 3: Import Topic")
from backend.app.userecho.model.topic import Topic

print(f"  OK: {Topic}")

print("\nTest 4: Check Tenant.merge_suggestions")
print(f"  OK: {Tenant.merge_suggestions}")

print("\nTest 5: Check MergeSuggestion.tenant")
print(f"  OK: {MergeSuggestion.tenant}")

print("\n[SUCCESS] No circular import issues!")
