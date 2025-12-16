import json
import os
import matplotlib.pyplot as plt
import matplotlib
from collections import defaultdict

matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

def get_hierarchical_stats(data_dir):
    hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
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
                        parts = rel_path.split(os.sep)
                        
                        if len(parts) >= 3:
                            cat1 = parts[0]
                            
                            if len(parts) == 3:
                                cat2 = parts[1]
                                filename = os.path.splitext(parts[-1])[0]
                            elif len(parts) == 4:
                                cat2 = f"{parts[1]}/{parts[2]}"
                                filename = os.path.splitext(parts[-1])[0]
                            elif len(parts) >= 5:
                                cat2 = f"{parts[1]}/{parts[2]}/{parts[3]}"
                                filename = os.path.splitext(parts[-1])[0]
                            
                            hierarchy[cat1][cat2][filename] = count
                except:
                    pass
    
    return hierarchy

def create_nested_pie_chart(hierarchy):
    fig, axes = plt.subplots(2, 2, figsize=(20, 20))
    fig.suptitle('PRISM Data Distribution', fontsize=24, fontweight='bold', y=0.995)
    
    categories = ['IFE', 'KE', 'KM', 'RE']
    colors_map = {
        'IFE': plt.cm.Blues,
        'KE': plt.cm.Greens,
        'KM': plt.cm.Oranges,
        'RE': plt.cm.Purples
    }
    
    for idx, cat in enumerate(categories):
        ax = axes[idx // 2, idx % 2]
        
        if cat not in hierarchy:
            continue
        
        subcats = hierarchy[cat]
        
        labels = []
        sizes = []
        colors = []
        explode = []
        
        cmap = colors_map[cat]
        subcat_list = sorted(subcats.items())
        n_subcats = len(subcat_list)
        
        for i, (subcat, files) in enumerate(subcat_list):
            subcat_total = sum(files.values())
            
            for j, (filename, count) in enumerate(sorted(files.items())):
                label = f"{subcat}\n{filename}\n({count})"
                labels.append(label)
                sizes.append(count)
                
                color_idx = (i * 0.7 + j * 0.3 / len(files)) / n_subcats
                colors.append(cmap(0.3 + color_idx * 0.6))
                
                if i == 0 and j == 0:
                    explode.append(0.05)
                else:
                    explode.append(0.02)
        
        total = sum(sizes)
        
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=None,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            explode=explode,
            pctdistance=0.85,
            textprops={'fontsize': 8}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(7)
        
        ax.set_title(f'{cat} ({total} items)', fontsize=16, fontweight='bold', pad=20)
        
        ax.legend(
            wedges, 
            labels,
            title=f"{cat} Files",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=7,
            title_fontsize=10
        )
    
    plt.tight_layout()
    plt.savefig('/Users/yydoog/Desktop/PRISM/Data/data_distribution.png', dpi=300, bbox_inches='tight')
    print("Pie chart saved to: /Users/yydoog/Desktop/PRISM/Data/data_distribution.png")
    
    create_summary_chart(hierarchy)

def create_summary_chart(hierarchy):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 12))
    fig.suptitle('PRISM Data Summary', fontsize=24, fontweight='bold')
    
    cat_totals = {}
    for cat, subcats in hierarchy.items():
        total = sum(sum(files.values()) for files in subcats.values())
        cat_totals[cat] = total
    
    colors1 = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6']
    wedges1, texts1, autotexts1 = ax1.pie(
        cat_totals.values(),
        labels=[f'{k}\n({v})' for k, v in cat_totals.items()],
        autopct='%1.1f%%',
        startangle=90,
        colors=colors1,
        explode=[0.05, 0.05, 0.05, 0.05],
        textprops={'fontsize': 14, 'fontweight': 'bold'}
    )
    
    for autotext in autotexts1:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(14)
    
    ax1.set_title('By Main Category', fontsize=18, fontweight='bold', pad=20)
    
    subcat_data = []
    subcat_labels = []
    subcat_colors = []
    
    color_maps = {
        'IFE': plt.cm.Blues,
        'KE': plt.cm.Greens,
        'KM': plt.cm.Oranges,
        'RE': plt.cm.Purples
    }
    
    for cat in ['IFE', 'KE', 'KM', 'RE']:
        if cat not in hierarchy:
            continue
        subcats = hierarchy[cat]
        cmap = color_maps[cat]
        n = len(subcats)
        
        for i, (subcat, files) in enumerate(sorted(subcats.items())):
            total = sum(files.values())
            subcat_data.append(total)
            subcat_labels.append(f'{cat}-{subcat}\n({total})')
            subcat_colors.append(cmap(0.4 + (i / n) * 0.5))
    
    wedges2, texts2, autotexts2 = ax2.pie(
        subcat_data,
        labels=subcat_labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=subcat_colors,
        explode=[0.02] * len(subcat_data),
        textprops={'fontsize': 10}
    )
    
    for autotext in autotexts2:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)
    
    ax2.set_title('By Subcategory', fontsize=18, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('/Users/yydoog/Desktop/PRISM/Data/data_summary.png', dpi=300, bbox_inches='tight')
    print("Summary chart saved to: /Users/yydoog/Desktop/PRISM/Data/data_summary.png")

def main():
    data_dir = '/Users/yydoog/Desktop/PRISM/Data'
    hierarchy = get_hierarchical_stats(data_dir)
    create_nested_pie_chart(hierarchy)
    print("\nVisualization complete!")

if __name__ == '__main__':
    main()
