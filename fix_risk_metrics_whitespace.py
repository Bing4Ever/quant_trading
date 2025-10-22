#!/usr/bin/env python3
"""Clean trailing whitespace from risk_metrics.py"""

def clean_whitespace():
    """Remove trailing whitespace from all lines."""
    file_path = 'risk_management/risk_metrics.py'
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Remove trailing whitespace from each line
    cleaned_lines = []
    for line in lines:
        cleaned_lines.append(line.rstrip() + '\n')
    
    # Ensure final newline
    if cleaned_lines and not cleaned_lines[-1].endswith('\n'):
        cleaned_lines[-1] += '\n'
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(cleaned_lines)
    
    print(f"Cleaned trailing whitespace from {len(lines)} lines in {file_path}")

if __name__ == '__main__':
    clean_whitespace()