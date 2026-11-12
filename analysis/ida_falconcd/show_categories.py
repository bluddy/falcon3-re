"""Show category summary from function discovery."""
import json

with open('all_functions_categorized.json') as f:
    data = json.load(f)

print("="*80)
print(f"FALCON 3.0 FUNCTION CATEGORIZATION")
print(f"Total Functions: {data['total_functions']}")
print("="*80)

categories = data['categories']

# Sort by function count descending
sorted_cats = sorted(categories.items(), key=lambda x: x[1]['count'], reverse=True)

for cat_name, cat_data in sorted_cats:
    print(f"\n{cat_name.upper()}: {cat_data['count']} functions")
    print(f"  Total size: {cat_data['total_size']:,} bytes")
    print(f"  Avg size: {cat_data['total_size']/cat_data['count']:.1f} bytes")
    print(f"  Avg calls: {cat_data['total_calls']/cat_data['count']:.1f}")
    
    # Show first 5 function names
    print(f"  Sample functions:")
    for func in cat_data['functions'][:5]:
        print(f"    - {func['name']} ({func['size']} bytes)")

print("\n" + "="*80)
print("SYSTEM COMPARISON")
print("="*80)
print(f"{'System':<15} {'Functions':<12} {'Size (KB)':<12} {'% of Total':<12}")
print("-"*80)

total_size = sum(cat['total_size'] for cat in categories.values())

for cat_name, cat_data in sorted_cats:
    pct = (cat_data['total_size'] / total_size * 100) if total_size > 0 else 0
    print(f"{cat_name:<15} {cat_data['count']:<12} {cat_data['total_size']/1024:<12.1f} {pct:<12.1f}%")
