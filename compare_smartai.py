import os
import filecmp

def compare_dirs(dir1, dir2):
    dcmp = filecmp.dircmp(dir1, dir2)
    print(f'Diffing {dir1} and {dir2}')
    if dcmp.left_only: print(f'Only in {dir1}: {dcmp.left_only}')
    if dcmp.right_only: print(f'Only in {dir2}: {dcmp.right_only}')
    if dcmp.diff_files: print(f'Differing files: {dcmp.diff_files}')
    for sub in dcmp.common_dirs:
        if sub not in ['.git', '.idea', '__pycache__', '.venv', 'logs', 'output', 'data', '.pytest_cache']:
            compare_dirs(os.path.join(dir1, sub), os.path.join(dir2, sub))

compare_dirs('e:/Projects/SLT-Billing-System/Models/SmartAI_Bill', 'e:/Projects/SLT-Billing-System/Models/SmartAI_Bill_y')
