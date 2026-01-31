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
import atexit
from collections import deque

app = Flask(__name__)
CORS(app)

# Логи в памяти (последние 500 строк)
log_buffer = deque(maxlen=500)

def log(message):
    """Логирует сообщение в консоль и в буфер"""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    log_buffer.append(log_line)

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

# Глобальные счетчики (не сбрасываются)
global_stats = {
    "total_spawned": 0,
    "total_killed": 0
}

# Счетчики и блокировки
backup_counter = 0
data_lock = Lock()
background_thread = None
stop_background = False
initialized = False

def load_data():
    """Загружает данные серверов"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                # Загружаем серверы и глобальные счетчики
                if isinstance(data, dict):
                    if 'servers' in data:
                        return data['servers'], data.get('global_stats', {"total_spawned": 0, "total_killed": 0})
                    return data, {"total_spawned": 0, "total_killed": 0}
        except:
            pass
    return {}, {"total_spawned": 0, "total_killed": 0}

def save_data():
    """Сохраняет данные серверов и глобальные счетчики"""
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'servers': servers,
                'global_stats': global_stats
            }, f, indent=2)
    except Exception as e:
        log(f"Failed to save data: {e}")

def load_history():
    """Загружает историю"""
    global history
    
    # Сначала пробуем загрузить из Gist (приоритет)
    if GIST_TOKEN and GIST_ID:
        try:
            log("[HISTORY] Attempting to load from Gist...")
            history_from_gist = load_from_gist()
            if history_from_gist and 'timestamps' in history_from_gist and len(history_from_gist['timestamps']) > 0:
                history = history_from_gist
                log(f"[HISTORY] Loaded {len(history['timestamps'])} points from Gist")
                save_history()  # Сохраняем локально
                cleanup_old_history()
                log(f"[HISTORY] After cleanup: {len(history['timestamps'])} points")
                return
            else:
                log("[HISTORY] Gist is empty or invalid")
        except Exception as e:
            log(f"[HISTORY] Failed to load from Gist: {e}")
            import traceback
            traceback.print_exc()
    else:
        log("[HISTORY] Gist not configured, skipping")
    
    # Если Gist не сработал, пробуем локальный файл
    if HISTORY_FILE.exists():
        try:
            log(f"[HISTORY] Loading from local file: {HISTORY_FILE}")
            with open(HISTORY_FILE, 'r') as f:
                loaded = json.load(f)
                if loaded and 'timestamps' in loaded and len(loaded['timestamps']) > 0:
                    history = loaded
                    log(f"[HISTORY] Loaded {len(history['timestamps'])} points from local file")
                    cleanup_old_history()
                    log(f"[HISTORY] After cleanup: {len(history['timestamps'])} points")
                    return
        except Exception as e:
            log(f"[HISTORY] Failed to load from local file: {e}")
            import traceback
            traceback.print_exc()
    else:
        log(f"[HISTORY] Local file does not exist: {HISTORY_FILE}")
    
    log("[HISTORY] No history found, starting fresh")

def save_history():
    """Сохраняет историю локально"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        log(f"Failed to save history: {e}")

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
        log(f"[HISTORY] Cleaned up old data, {len(valid_indices)} points remaining")

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
        if backup_counter % 2 == 0 and GIST_TOKEN and GIST_ID:
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
            log(f"[BACKUP] Successfully backed up to Gist ({len(history['timestamps'])} points)")
        else:
            log(f"[BACKUP] Failed to backup to Gist: {response.status_code}")
    except Exception as e:
        log(f"[BACKUP] Error backing up to Gist: {e}")

def load_from_gist():
    """Загружает историю из GitHub Gist"""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GIST_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        log(f"[GIST] Loading from {url}")
        response = requests.get(url, headers=headers, timeout=10)
        log(f"[GIST] Response status: {response.status_code}")
        
        if response.status_code == 200:
            gist_data = response.json()
            if 'files' in gist_data and 'stats_history.json' in gist_data['files']:
                content = gist_data['files']['stats_history.json']['content']
                data = json.loads(content)
                log(f"[GIST] Successfully loaded {len(data.get('timestamps', []))} points")
                return data
            else:
                log(f"[GIST] File 'stats_history.json' not found in gist")
                log(f"[GIST] Available files: {list(gist_data.get('files', {}).keys())}")
        else:
            log(f"[GIST] Failed with status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        log(f"[GIST] Error loading from Gist: {e}")
    return None

def get_stats():
    """Возвращает текущую статистику"""
    current_time = time.time()
    # Сервер считается активным если отправлял данные в последние 10 секунд (2 пропущенных пакета)
    active_servers = {
        sid: data for sid, data in servers.items()
        if current_time - data['last_seen'] < 10
    }
    
    servers_online = len(active_servers)
    bots_active = sum(data['bots_count'] for data in active_servers.values())
    
    # Используем глобальные счетчики вместо суммы по серверам
    bots_spawned_total = global_stats['total_spawned']
    bots_killed_total = global_stats['total_killed']
    
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
            # Инициализируем сервер если новый
            if server_id not in servers:
                servers[server_id] = {
                    'bots_spawned_total': 0,
                    'bots_killed_total': 0
                }
            
            # Обновляем глобальные счетчики (только если значения увеличились)
            old_spawned = servers[server_id].get('bots_spawned_total', 0)
            old_killed = servers[server_id].get('bots_killed_total', 0)
            new_spawned = data.get('bots_spawned_total', 0)
            new_killed = data.get('bots_killed_total', 0)
            
            if new_spawned > old_spawned:
                global_stats['total_spawned'] += (new_spawned - old_spawned)
            if new_killed > old_killed:
                global_stats['total_killed'] += (new_killed - old_killed)
            
            # Обновляем данные сервера
            servers[server_id].update({
                'bots_count': data.get('bots_count', 0),
                'bots_spawned_total': new_spawned,
                'bots_killed_total': new_killed,
                'mod_version': data.get('mod_version', 'unknown'),
                'minecraft_version': data.get('minecraft_version', 'unknown'),
                'last_seen': time.time()
            })
            
            save_data()
        
        # НЕ добавляем точку здесь - точки добавляются только фоновым сборщиком каждые 30 секунд
        log(f"[STATS] Received from {server_id[:8]}... - Bots: {data.get('bots_count', 0)}, Spawned: {new_spawned}, Killed: {new_killed}")
        
        return jsonify({"success": True}), 200
        
    except Exception as e:
        log(f"Error in receive_stats: {e}")
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
        "gist_enabled": bool(GIST_TOKEN and GIST_ID),
        "gist_id": GIST_ID if GIST_ID else None,
        "backup_counter": backup_counter,
        "next_backup_in": 120 - (backup_counter % 120) if GIST_TOKEN and GIST_ID else None,
        "global_stats": global_stats
    }), 200

@app.route('/api/backup', methods=['POST'])
def manual_backup():
    """Ручной backup в Gist (для отладки)"""
    if not GIST_TOKEN or not GIST_ID:
        return jsonify({"error": "Gist not configured"}), 400
    
    try:
        backup_to_gist()
        return jsonify({"success": True, "message": "Backup completed"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-gist', methods=['GET'])
def test_gist():
    """Тестирует загрузку из Gist (для отладки)"""
    if not GIST_TOKEN or not GIST_ID:
        return jsonify({"error": "Gist not configured"}), 400
    
    try:
        data = load_from_gist()
        if data:
            return jsonify({
                "success": True,
                "data_points": len(data.get('timestamps', [])),
                "first_timestamp": data.get('timestamps', [None])[0] if data.get('timestamps') else None,
                "last_timestamp": data.get('timestamps', [None])[-1] if data.get('timestamps') else None,
                "keys": list(data.keys())
            }), 200
        else:
            return jsonify({"error": "Failed to load from Gist"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reload-history', methods=['POST'])
def reload_history():
    """Перезагружает историю из Gist (для отладки)"""
    if not GIST_TOKEN or not GIST_ID:
        return jsonify({"error": "Gist not configured"}), 400
    
    try:
        load_history()
        return jsonify({
            "success": True,
            "data_points": len(history['timestamps']),
            "message": "History reloaded"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Возвращает последние логи"""
    try:
        lines = request.args.get('lines', 100, type=int)
        lines = min(lines, 500)  # Максимум 500 строк
        
        logs_list = list(log_buffer)
        if lines < len(logs_list):
            logs_list = logs_list[-lines:]
        
        return jsonify({
            "logs": logs_list,
            "total_lines": len(log_buffer),
            "returned_lines": len(logs_list)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def background_stats_collector():
    """Фоновый поток для сбора статистики каждые 30 секунд"""
    global stop_background
    log("[BACKGROUND] Stats collector started")
    
    while not stop_background:
        try:
            # Ждем 30 секунд
            for _ in range(30):
                if stop_background:
                    break
                time.sleep(1)
            
            if stop_background:
                break
            
            # Добавляем точку каждые 30 секунд (независимо от серверов)
            stats = get_stats()
            add_to_history(stats)
            log(f"[BACKGROUND] Added history point - Servers: {stats['servers_online']}, Bots: {stats['bots_active']}, Spawned: {stats['bots_spawned_total']}, Killed: {stats['bots_killed_total']}")
            
        except Exception as e:
            log(f"[BACKGROUND] Error: {e}")
    
    log("[BACKGROUND] Stats collector stopped")

def start_background_collector():
    """Запускает фоновый сборщик статистики"""
    global background_thread
    if background_thread is None or not background_thread.is_alive():
        background_thread = Thread(target=background_stats_collector, daemon=True)
        background_thread.start()

def stop_background_collector():
    """Останавливает фоновый сборщик"""
    global stop_background
    stop_background = True
    if background_thread:
        background_thread.join(timeout=5)

def initialize():
    """Инициализация при старте приложения"""
    global initialized, servers, global_stats, history
    
    if initialized:
        return
    
    log("[STARTUP] Starting PVPBOT Stats Backend...")
    log(f"[STARTUP] GIST_TOKEN: {'SET' if GIST_TOKEN else 'NOT SET'}")
    log(f"[STARTUP] GIST_ID: {GIST_ID if GIST_ID else 'NOT SET'}")
    
    # Загружаем данные при старте
    try:
        servers_loaded, global_stats_loaded = load_data()
        servers.update(servers_loaded)
        global_stats.update(global_stats_loaded)
        log(f"[STARTUP] Loaded {len(servers)} servers from local storage")
    except Exception as e:
        log(f"[STARTUP] Failed to load servers: {e}")
    
    try:
        load_history()
        log(f"[STARTUP] History loaded: {len(history['timestamps'])} points")
        
        # Если история не загрузилась, попробуем еще раз через 10 секунд
        if len(history['timestamps']) == 0 and GIST_TOKEN and GIST_ID:
            log("[STARTUP] History is empty, will retry in 10 seconds...")
            def retry_load():
                time.sleep(10)
                log("[STARTUP] Retrying history load...")
                load_history()
                log(f"[STARTUP] After retry: {len(history['timestamps'])} points")
            Thread(target=retry_load, daemon=True).start()
    except Exception as e:
        log(f"[STARTUP] Failed to load history: {e}")
        import traceback
        traceback.print_exc()
    
    log(f"[STARTUP] Total spawned: {global_stats['total_spawned']}")
    log(f"[STARTUP] Total killed: {global_stats['total_killed']}")
    log(f"[STARTUP] Gist backup: {'enabled' if GIST_TOKEN and GIST_ID else 'disabled'}")
    
    # Запускаем фоновый сборщик статистики
    start_background_collector()
    
    # Регистрируем остановку при выходе
    atexit.register(stop_background_collector)
    
    initialized = True
    log("[STARTUP] Initialization complete")

# Инициализируем при импорте модуля (после определения всех функций)
initialize()

if __name__ == '__main__':
    # Если запускаем напрямую через python
    port = int(os.environ.get('PORT', 5000))
    log(f"[STARTUP] Starting development server on port {port}")
    app.run(host='0.0.0.0', port=port)
