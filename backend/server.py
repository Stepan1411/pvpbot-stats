#!/usr/bin/env python3
"""
Простой backend для сбора статистики PVPBOT
Можно разместить на: Render, Railway, Heroku (бесплатно)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с других доменов

# Файл для хранения данных
DATA_FILE = Path("stats_data.json")
STATS_FILE = Path("../docs/data/stats.json")  # Для GitHub Pages

# Хранилище серверов (в памяти)
servers = {}

def load_data():
    """Загружает данные из файла"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_data():
    """Сохраняет данные в файл"""
    with open(DATA_FILE, 'w') as f:
        json.dump(servers, f, indent=2)

def update_stats_json():
    """Обновляет stats.json для GitHub Pages"""
    # Удаляем старые серверы (не отправляли данные больше 2 часов)
    current_time = time.time()
    active_servers = {
        sid: data for sid, data in servers.items()
        if current_time - data['last_seen'] < 7200  # 2 часа
    }
    
    # Подсчитываем статистику
    servers_online = len(active_servers)
    bots_active = sum(data['bots_count'] for data in active_servers.values())
    
    stats = {
        "servers_online": servers_online,
        "bots_active": bots_active,
        "total_downloads": 0,  # TODO: получать из GitHub API
        "mod_version": "1.0.0",
        "last_update": datetime.utcnow().isoformat() + "Z",
        "servers": [
            {
                "id": sid[:8] + "...",  # Скрываем полный ID
                "bots": data['bots_count'],
                "last_seen": datetime.fromtimestamp(data['last_seen']).isoformat() + "Z"
            }
            for sid, data in active_servers.items()
        ]
    }
    
    # Сохраняем
    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f, indent=2)
    
    return stats

@app.route('/api/stats', methods=['POST'])
def receive_stats():
    """Принимает статистику от серверов"""
    try:
        data = request.json
        
        # Валидация
        if not data or 'server_id' not in data:
            return jsonify({"error": "Invalid data"}), 400
        
        server_id = data['server_id']
        bots_count = data.get('bots_count', 0)
        
        # Сохраняем данные
        servers[server_id] = {
            'bots_count': bots_count,
            'mod_version': data.get('mod_version', 'unknown'),
            'minecraft_version': data.get('minecraft_version', 'unknown'),
            'last_seen': time.time()
        }
        
        # Сохраняем в файл
        save_data()
        
        # Обновляем stats.json
        update_stats_json()
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Возвращает агрегированную статистику"""
    try:
        stats = update_stats_json()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check для хостинга"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Загружаем данные при старте
    servers = load_data()
    
    # Запускаем сервер
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
