import json
import os
import random

def balance_category(data_dir, category, target_count):
    files_data = {}
    total_count = 0
    
    cat_dir = os.path.join(data_dir, category)
    for root, dirs, files in os.walk(cat_dir):
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    files_data[filepath] = data
                    total_count += len(data)
    
    if total_count <= target_count:
        print(f"{category} 当前 {total_count} 条，无需删减")
        return
    
    keep_ratio = target_count / total_count
    print(f"{category} 当前 {total_count} 条，目标 {target_count} 条，保留比例 {keep_ratio:.2%}")
    
    for filepath, data in files_data.items():
        original_count = len(data)
        new_count = max(1, int(original_count * keep_ratio))
        
        random.seed(42)
        random.shuffle(data)
        new_data = data[:new_count]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        
        rel_path = os.path.relpath(filepath, data_dir)
        print(f"  {rel_path}: {original_count} → {new_count} 条")

def main():
    data_dir = '/Users/yydoog/Desktop/PRISM/Data'
    
    print("开始均衡数据...")
    print("\n" + "="*80)
    balance_category(data_dir, 'KE', 3000)
    
    print("\n" + "="*80)
    balance_category(data_dir, 'RE', 3000)
    
    print("\n" + "="*80)
    print("完成！运行 detailed_stats.py 查看结果")

if __name__ == '__main__':
    main()
