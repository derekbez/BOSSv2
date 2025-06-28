#!/usr/bin/env python3
"""
Recursively delete all __pycache__ folders in the project.
Usage: python clean_pycache.py
"""
import os
import shutil

def remove_pycache_dirs(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            print(f"Removing: {pycache_path}")
            shutil.rmtree(pycache_path)
            dirnames.remove('__pycache__')  # Prevent further walk into it

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    remove_pycache_dirs(project_root)
    print("All __pycache__ folders removed.")
