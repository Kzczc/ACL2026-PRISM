import json
import os

def get_json_stats(data_dir):
    stats = {}
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, data_dir)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        count = len(data)
                        stats[rel_path] = count
                except Exception as e:
                    stats[rel_path] = f"Error: {str(e)}"
    
    return stats

def print_stats_by_category(stats):
    categories = {
        'IFE': {},
        'KE': {},
        'KM': {},
        'RE': {}
    }
    
    for path, count in sorted(stats.items()):
        for cat in categories.keys():
            if path.startswith(cat):
                categories[cat][path] = count
                break
    
    total = 0
    
    for cat_name in ['IFE', 'KE', 'KM', 'RE']:
        cat_files = categories[cat_name]
        if not cat_files:
            continue
        
        print(f"\n{'='*80}")
        print(f"{cat_name} 类别")
        print(f"{'='*80}")
        
        cat_total = 0
        for path, count in sorted(cat_files.items()):
            if isinstance(count, int):
                print(f"{path:70s} {count:6d} 条")
                cat_total += count
            else:
                print(f"{path:70s} {count}")
        
        print(f"{'-'*80}")
        print(f"小计: {cat_total} 条")
        total += cat_total
    
    print(f"\n{'='*80}")
    print(f"总计: {len(stats)} 个文件，共 {total} 条数据")
    print(f"{'='*80}")

def main():
    data_dir = '/Users/yydoog/Desktop/PRISM/Data'
    stats = get_json_stats(data_dir)
    print_stats_by_category(stats)

if __name__ == '__main__':
    main()
