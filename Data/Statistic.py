import json
import os
import csv

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

def save_stats_to_csv(stats, output_file):
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
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'File Path', 'Count'])
        
        total = 0
        for cat_name in ['IFE', 'KE', 'KM', 'RE']:
            cat_files = categories[cat_name]
            if not cat_files:
                continue
            
            cat_total = 0
            for path, count in sorted(cat_files.items()):
                if isinstance(count, int):
                    writer.writerow([cat_name, path, count])
                    cat_total += count
                else:
                    writer.writerow([cat_name, path, count])
            
            writer.writerow([cat_name, 'Subtotal', cat_total])
            total += cat_total
        
        writer.writerow(['Total', f'{len(stats)} files', total])
    
    print(f"Statistics saved to {output_file}")
    print(f"Total: {len(stats)} files, {total} records")

def main():
    data_dir = '/Users/yydoog/Desktop/PRISM/Data'
    output_file = os.path.join(data_dir, 'statistics.csv')
    stats = get_json_stats(data_dir)
    save_stats_to_csv(stats, output_file)

if __name__ == '__main__':
    main()
