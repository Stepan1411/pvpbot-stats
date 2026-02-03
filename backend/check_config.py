#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации перед деплоем
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✓ Loaded .env from {env_path}")
    else:
        print(f"⚠ .env file not found at {env_path}")
        print("  Copy .env.example to .env and fill in the values")
except ImportError:
    print("⚠ python-dotenv not installed")
    print("  Run: pip install python-dotenv")

print("\n=== Configuration Check ===\n")

# Проверяем переменные окружения
required_vars = {
    'GITHUB_REPO': 'GitHub repository URL',
    'GITHUB_TOKEN': 'GitHub Personal Access Token',
    'ADMIN_PASSWORD': 'Admin panel password',
    'GITHUB_BRANCH': 'Git branch (usually main)'
}

all_ok = True
for var, description in required_vars.items():
    value = os.environ.get(var)
    if value:
        if var == 'GITHUB_TOKEN':
            print(f"✓ {var}: {'*' * 20} (hidden)")
        elif var == 'ADMIN_PASSWORD':
            print(f"✓ {var}: {'*' * len(value)} (hidden)")
        else:
            print(f"✓ {var}: {value}")
    else:
        print(f"✗ {var}: NOT SET - {description}")
        all_ok = False

print("\n=== Directory Check ===\n")

# Проверяем директории
data_dir = Path(__file__).parent / 'data'
if data_dir.exists():
    print(f"✓ Data directory exists: {data_dir}")
    
    # Проверяем Git
    git_dir = data_dir / '.git'
    if git_dir.exists():
        print(f"✓ Git repository initialized")
    else:
        print(f"⚠ Git repository not initialized in data directory")
        print(f"  Run: cd {data_dir} && git init")
    
    # Проверяем файлы данных
    data_files = ['servers.json', 'global_stats.json', 'global_history.json']
    for filename in data_files:
        filepath = data_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✓ {filename}: {size} bytes")
        else:
            print(f"⚠ {filename}: not found (will be created on first run)")
else:
    print(f"⚠ Data directory not found: {data_dir}")
    print(f"  It will be created on first run")

print("\n=== Dependencies Check ===\n")

# Проверяем зависимости
dependencies = ['flask', 'flask_cors', 'dotenv']
for dep in dependencies:
    try:
        __import__(dep)
        print(f"✓ {dep} installed")
    except ImportError:
        print(f"✗ {dep} NOT installed")
        all_ok = False

print("\n=== Summary ===\n")

if all_ok:
    print("✓ All checks passed! Ready to deploy.")
else:
    print("✗ Some checks failed. Please fix the issues above.")
    exit(1)
