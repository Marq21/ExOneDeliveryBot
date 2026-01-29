#!/usr/bin/env python3
import os
import shutil
import sys

def remove_dirs(root, dirs):
    """Удаление указанных директорий"""
    removed = 0
    dirs_to_remove = ['__pycache__', '.pytest_cache', '.mypy_cache', '.coverage']
    
    for dir_name in dirs_to_remove:
        if dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                shutil.rmtree(dir_path)
                removed += 1
                print(f"✅ Удалена папка: {dir_path}")
            except Exception as e:
                print(f"⚠️ Ошибка удаления {dir_path}: {e}")
    
    return removed

def remove_files(root, files):
    """Удаление указанных файлов"""
    removed = 0
    extensions_to_remove = ['.pyc', '.pyo', '.pyd', '.so', '.c', '.cpp']
    
    for file in files:
        if any(file.endswith(ext) for ext in extensions_to_remove):
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)
                removed += 1
                print(f"✅ Удален файл: {file_path}")
            except Exception as e:
                print(f"⚠️ Ошибка удаления {file_path}: {e}")
    
    return removed

def clean_project():
    """Очистка всего кэша проекта"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    print(f"🧹 Очищаем проект: {project_root}")
    print("=" * 50)
    
    total_removed = 0
    
    for root, dirs, files in os.walk(project_root):
        total_removed += remove_dirs(root, dirs)
        total_removed += remove_files(root, files)
    
    # Удаляем .pyc файлы в корне проекта
    for item in os.listdir(project_root):
        if item.endswith('.pyc'):
            try:
                os.remove(os.path.join(project_root, item))
                total_removed += 1
                print(f"✅ Удален файл: {item}")
            except Exception as e:
                print(f"⚠️ Ошибка удаления {item}: {e}")
    
    print("=" * 50)
    print(f"🎯 Всего удалено: {total_removed} объектов")
    
    return total_removed

if __name__ == '__main__':
    clean_project()