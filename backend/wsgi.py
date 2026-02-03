"""
WSGI конфигурация для PythonAnywhere
"""
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
project_home = '/home/YOUR_USERNAME/pvpbot-stats/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Импортируем приложение
from server import app as application

# Инициализируем при старте
from server import initialize
initialize()
