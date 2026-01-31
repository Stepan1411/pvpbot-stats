#!/usr/bin/env python3
"""
Backend для сбора статистики PVPBOT
С поддержкой Railway Volume и GitHub Gist backup
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time
import os
import requests
from datetime import datetime
from pathlib import Path
from threading import Thread, Lock

app = Flask(__name__)
CORS(app)

# Папка для данных (Railway Volume)
DATA_DIR = Path(os.environ.get('DATA_DIR', './data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "stats_data.json"
HISTORY_FILE = DATA_DIR / "stats_history.json"

# GitHub Gist для backup
GIST_TOKEN = os.environ.get('GITHUB_GIST_TOKEN', '')
GIST_ID = os.environ.get('GITHUB_GIST_ID', '')

# Хранилище
servers = {}
history = {
    "timestamps": [],
    "servers": [],
    "bots": [],
    "spawned": [],
    "killed": []
}

# Счетчики и блокировки
backup_counter = 0
data_lock = Lock()

def load_data():
    """Загружает данные серверов"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_data():
    """Сохраняет данные серверов"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(servers, f, indent=2)
    except Exception as e:
        print(f"Failed to save data: {e}")

def load_history():
    """Загружает историю"""
    global history
    
    # Пробуем загрузить из локального файла
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                loaded = json.load(f)
                if loaded and 'timestamps' in loaded:
                    history = loaded
                    print(f"[HISTORY] Loaded {len(history['timestamps'])} points from file")
                    cleanup_old_history()
                    return
        except Exception as e:
            print(f"Failed to load history from file: {e}")
    
    # Если локального файла нет, пробуем загрузить из Gist
    if GIST_TOKEN and GIST_ID:
        try:
            history_from_gist = load_from_gist()
            if history_from_gist:
                history = history_from_gist
                save_history()  # Сохраняем локально
                print(f"[HISTORY] Loaded {len(history['timestamps'])} points from Gist")
        except Exception as e:
            print(f"Failed to load history from Gist: {e}")

def save_history():
    """Сохраняет историю локально"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Failed to save history: {e}")

def cleanup_old_history():
    """Удаляет данные старше 1 года"""
    one_year_ago = time.time() - (365 * 24 * 60 * 60)
    valid_indices = [i for i, ts in enumerate(history['timestamps']) if ts > one_year_ago]
    
    if len(valid_indices) < len(history['timestamps']):
        history['timestamps'] = [history['timestamps'][i] for i in valid_indices]
        history['servers'] = [history['servers'][i] for i in valid_indices]
        history['bots'] = [history['bots'][i] for i in valid_indices]
        history['spawned'] = [history['spawned'][i] for i in valid_indices]
        history['killed'] = [history['killed'][i] for i in valid_indices]
        print(f"[HISTORY] Cleaned up old data, {len(valid_indices)} points remaining")

def add_to_history(stats):
    """Добавляет точку в историю"""
    global backup_counter
    
    with data_lock:
        current_time = time.time()
        
        history['timestamps'].append(current_time)
        history['servers'].append(stats['servers_online'])
        history['bots'].append(stats['bots_active'])
        history['spawned'].append(stats['bots_spawned_total'])
        history['killed'].append(stats['bots_killed_total'])
        
        # Ограничиваем размер
        max_points = 100000
        if len(history['timestamps']) > max_points:
            history['timestamps'] = history['timestamps'][-max_points:]
            history['servers'] = history['servers'][-max_points:]
            history['bots'] = history['bots'][-max_points:]
            history['spawned'] = history['spawned'][-max_points:]
            history['killed'] = history['killed'][-max_points:]
        
        # Сохраняем локально каждые 10 точек
        backup_counter += 1
        if backup_counter % 10 == 0:
            save_history()
        
        # Backup в Gist каждые 120 точек (10 минут при обновлении каждые 5 сек)
        if backup_counter % 120 == 0 and GIST_TOKEN and GIST_ID:
            Thread(target=backup_to_gist, daemon=True).start()

def backup_to_gist():
    """Резервное копирование в GitHub Gist"""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GIST_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "files": {
                "stats_history.json": {
                    "content": json.dumps(history, indent=2)
                }
            }
        }
        
        response = requests.patch(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            print(f"[BACKUP] Successfully backed up to Gist ({len(history['timestamps'])} points)")
        else:
            print(f"[BACKUP] Failed to backup to Gist: {response.status_code}")
    except Exception as e:
        print(f"[BACKUP] Error backing up to Gist: {e}")

def load_from_gist():
    """Загружает историю из GitHub Gist"""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GIST_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            gist_data = response.json()
            if 'files' in gist_data and 'stats_history.json' in gist_data['files']:
                content = gist_data['files']['stats_history.json']['content']
                return json.loads(content)
    except Exception as e:
        print(f"[BACKUP] Error loading from Gist: {e}")
    return None

def get_stats():
    """Возвращает текущую статистику"""
    current_time = time.time()
    active_servers = {
        sid: data for sid, data in servers.items()
        if current_time - data['last_seen'] < 7200
    }
    
    servers_online = len(active_servers)
    bots_active = sum(data['bots_count'] for data in active_servers.values())
    bots_spawned_total = sum(data.get('bots_spawned_total', 0) for data in active_servers.values())
    bots_killed_total = sum(data.get('bots_killed_total', 0) for data in active_servers.values())
    
    return {
        "servers_online": servers_online,
        "bots_active": bots_active,
        "bots_spawned_total": bots_spawned_total,
        "bots_killed_total": bots_killed_total,
        "total_downloads": 0,
        "mod_version": "1.0.0",
        "last_update": datetime.utcnow().isoformat() + "Z",
        "servers": [
            {
                "id": sid[:8] + "...",
                "bots": data['bots_count'],
                "last_seen": datetime.fromtimestamp(data['last_seen']).isoformat() + "Z"
            }
            for sid, data in active_servers.items()
        ]
    }

@app.route('/api/stats', methods=['POST'])
def receive_stats():
    """Принимает статистику от серверов"""
    try:
        data = request.json
        
        if not data or 'server_id' not in data:
            return jsonify({"error": "Invalid data"}), 400
        
        server_id = data['server_id']
        
        with data_lock:
            if server_id not in servers:
                servers[server_id] = {
                    'bots_spawned_total': 0,
                    'bots_killed_total': 0
                }
            
            servers[server_id].update({
                'bots_count': data.get('bots_count', 0),
                'mod_version': data.get('mod_version', 'unknown'),
                'minecraft_version': data.get('minecraft_version', 'unknown'),
                'last_seen': time.time()
            })
            
            if 'bots_spawned_total' in data:
                servers[server_id]['bots_spawned_total'] = data['bots_spawned_total']
            if 'bots_killed_total' in data:
                servers[server_id]['bots_killed_total'] = data['bots_killed_total']
            
            save_data()
        
        # Добавляем в историю
        stats = get_stats()
        add_to_history(stats)
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats_endpoint():
    """Возвращает текущую статистику"""
    try:
        stats = get_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history_endpoint():
    """Возвращает историю для графиков"""
    try:
        with data_lock:
            return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "data_points": len(history['timestamps']),
        "servers": len(servers),
        "gist_enabled": bool(GIST_TOKEN and GIST_ID)
    }), 200

if __name__ == '__main__':
    # Загружаем данные при старте
    servers = load_data()
    load_history()
    
    print(f"[STARTUP] Loaded {len(servers)} servers")
    print(f"[STARTUP] Loaded {len(history['timestamps'])} history points")
    print(f"[STARTUP] Gist backup: {'enabled' if GIST_TOKEN and GIST_ID else 'disabled'}")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
