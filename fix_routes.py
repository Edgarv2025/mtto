import os
import re

templates_dir = "templates"

replacements = [
    (r'url_for\([\'"]users[\'"]\)', r"url_for('auth.users')"),
    (r'url_for\([\'"]upload_logo[\'"]\)', r"url_for('reports.upload_logo')"),
    (r'url_for\([\'"]products[\'"]\)', r"url_for('products.products')"),
    (r'url_for\([\'"]upload_csv[\'"]\)', r"url_for('products.upload_csv')"),
    (r'url_for\([\'"]api_products[\'"]\)', r"url_for('products.api_products')"),
    (r'url_for\([\'"]items_dashboard[\'"]', r"url_for('maintenance.items_dashboard'"),
    (r'url_for\([\'"]delete_maintenance[\'"]', r"url_for('maintenance.delete_maintenance'"),
    (r'url_for\([\'"]update_item[\'"]', r"url_for('maintenance.update_item'"),
    (r'url_for\([\'"]api_suppliers[\'"]\)', r"url_for('suppliers.api_suppliers')"),
    (r'url_for\([\'"]dashboard_hash[\'"]\)', r"url_for('reports.dashboard_hash')"),
    (r'url_for\([\'"]dashboard[\'"]\)', r"url_for('reports.dashboard')"),
    (r'url_for\([\'"]maintenance[\'"]\)', r"url_for('maintenance.maintenance')"),
    (r'url_for\([\'"]maintenance_list[\'"]\)', r"url_for('maintenance.maintenance_list')"),
    (r'url_for\([\'"]suppliers[\'"]\)', r"url_for('suppliers.suppliers')"),
    (r'url_for\([\'"]reports[\'"]\)', r"url_for('reports.reports')"),
    (r'url_for\([\'"]logout[\'"]\)', r"url_for('auth.logout')"),
    (r'url_for\([\'"]login[\'"]\)', r"url_for('auth.login')")
]

for root, _, files in os.walk(templates_dir):
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            for old, new in replacements:
                content = re.sub(old, new, content)
            
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)

print("Template routes updated successfully.")
