// URL бэкенда Replit
const BACKEND_URL = 'https://pvpbot-stats--stepanksv141114.replit.app/api/stats';
const HISTORY_URL = 'https://pvpbot-stats--stepanksv141114.replit.app/api/history';
const FALLBACK_URL = 'data/stats.json';

// История данных
let historyData = {
    timestamps: [],
    servers: [],
    bots: [],
    spawned: [],
    killed: []
};

// Текущий период
let currentPeriod = {
    servers: '1h',
    bots: '1h'
};

// Графики
let serversChart = null;
let botsChart = null;

// Текущие значения
let currentValues = {
    servers: 0,
    bots: 0,
    spawned: 0,
    killed: 0
};

// Статус API
let apiAvailable = true;
let consecutiveFailures = 0;

// Theme Toggle
const themeSwitch = document.getElementById('theme-switch');
const currentTheme = localStorage.getItem('theme') || 'light';

if (currentTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    themeSwitch.checked = true;
}

themeSwitch.addEventListener('change', function() {
    if (this.checked) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    }
    updateChartColors();
});

// Загрузка истории с backend
async function loadHistory() {
    try {
        const response = await fetch(HISTORY_URL);
        if (response.ok) {
            const data = await response.json();
            if (data && data.timestamps && data.timestamps.length > 0) {
                // Конвертируем timestamps из секунд в миллисекунды
                historyData = {
                    timestamps: data.timestamps.map(ts => ts * 1000),
                    servers: data.servers || [],
                    bots: data.bots || [],
                    spawned: data.spawned || [],
                    killed: data.killed || []
                };
                console.log(`[HISTORY] Loaded ${historyData.timestamps.length} points from backend`);
                console.log(`[HISTORY] Time range: ${new Date(historyData.timestamps[0]).toLocaleString()} - ${new Date(historyData.timestamps[historyData.timestamps.length - 1]).toLocaleString()}`);
                return true;
            } else {
                console.warn('[HISTORY] No data received from backend');
            }
        } else {
            console.warn(`[HISTORY] Backend returned status ${response.status}`);
        }
    } catch (e) {
        console.error('[HISTORY] Failed to load from backend:', e);
    }
    return false;
}

// Загрузка статистики
async function loadStats() {
    try {
        let response;
        try {
            response = await fetch(BACKEND_URL);
            if (!response.ok) throw new Error('Backend unavailable');
            
            // API доступен
            if (!apiAvailable) {
                apiAvailable = true;
                consecutiveFailures = 0;
                hideApiBanner();
            }
        } catch (backendError) {
            console.log('Backend unavailable, using fallback data');
            consecutiveFailures++;
            
            // Показываем баннер после 2 неудачных попыток
            if (consecutiveFailures >= 2 && apiAvailable) {
                apiAvailable = false;
                showApiBanner();
            }
            
            response = await fetch(FALLBACK_URL);
        }
        
        const data = await response.json();
        
        // Обновляем значения с анимацией
        animateValue('servers-online', currentValues.servers, data.servers_online || 0);
        animateValue('bots-active', currentValues.bots, data.bots_active || 0);
        animateValue('bots-spawned', currentValues.spawned, data.bots_spawned_total || 0);
        animateValue('bots-killed', currentValues.killed, data.bots_killed_total || 0);
        
        currentValues.servers = data.servers_online || 0;
        currentValues.bots = data.bots_active || 0;
        currentValues.spawned = data.bots_spawned_total || 0;
        currentValues.killed = data.bots_killed_total || 0;
        
        const lastUpdate = new Date(data.last_update);
        document.getElementById('last-update').textContent = lastUpdate.toLocaleString();
        
    } catch (error) {
        console.error('Failed to load stats:', error);
        consecutiveFailures++;
        
        if (consecutiveFailures >= 2 && apiAvailable) {
            apiAvailable = false;
            showApiBanner();
        }
        
        document.getElementById('last-update').textContent = 'Failed to load';
    }
}

function showApiBanner() {
    const banner = document.getElementById('api-status-banner');
    if (banner) {
        banner.classList.remove('hidden');
    }
}

function hideApiBanner() {
    const banner = document.getElementById('api-status-banner');
    if (banner) {
        banner.classList.add('hidden');
    }
}

// Анимация чисел
function animateValue(elementId, startValue, endValue) {
    const element = document.getElementById(elementId);
    
    if (startValue === endValue) {
        element.textContent = endValue;
        return;
    }
    
    const duration = 500;
    const range = endValue - startValue;
    const increment = range / (duration / 16);
    let current = startValue;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= endValue) || (increment < 0 && current <= endValue)) {
            current = endValue;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// Фильтрация данных по периоду
function filterDataByPeriod(period) {
    const now = Date.now();
    let cutoff;
    
    switch(period) {
        case '1h':
            cutoff = now - (60 * 60 * 1000);
            break;
        case '1d':
            cutoff = now - (24 * 60 * 60 * 1000);
            break;
        case '1w':
            cutoff = now - (7 * 24 * 60 * 60 * 1000);
            break;
        case '1m':
            cutoff = now - (30 * 24 * 60 * 60 * 1000);
            break;
        case '1y':
            cutoff = now - (365 * 24 * 60 * 60 * 1000);
            break;
        default:
            cutoff = now - (60 * 60 * 1000);
    }
    
    const filtered = {
        timestamps: [],
        servers: [],
        bots: [],
        labels: []
    };
    
    // Проверяем что данные существуют
    if (!historyData.timestamps || historyData.timestamps.length === 0) {
        console.warn(`[FILTER] No history data available for period ${period}`);
        return filtered;
    }
    
    for (let i = 0; i < historyData.timestamps.length; i++) {
        if (historyData.timestamps[i] >= cutoff) {
            filtered.timestamps.push(historyData.timestamps[i]);
            filtered.servers.push(historyData.servers[i] || 0);
            filtered.bots.push(historyData.bots[i] || 0);
            
            const date = new Date(historyData.timestamps[i]);
            let label;
            if (period === '1h' || period === '1d') {
                label = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
            } else if (period === '1w') {
                label = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' });
            } else {
                label = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }
            filtered.labels.push(label);
        }
    }
    
    console.log(`[FILTER] Period ${period}: ${filtered.timestamps.length} points (from ${historyData.timestamps.length} total)`);
    
    return filtered;
}

// Инициализация графиков
function initCharts() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#eaeaea' : '#333333';
    const gridColor = isDark ? '#2a2a4e' : '#e0e0e0';
    
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        animation: false,  // Отключаем все анимации
        transitions: {
            active: { animation: { duration: 0 } },
            resize: { animation: { duration: 0 } },
            show: { animation: { duration: 0 } },
            hide: { animation: { duration: 0 } }
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                animation: {
                    duration: 200  // Только tooltip анимация
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    color: textColor,
                    precision: 0,
                    stepSize: 1
                },
                grid: {
                    color: gridColor
                }
            },
            x: {
                ticks: {
                    color: textColor,
                    maxRotation: 45,
                    minRotation: 45
                },
                grid: {
                    color: gridColor
                }
            }
        }
    };
    
    // График серверов
    const serversCtx = document.getElementById('serversChart').getContext('2d');
    const serversData = filterDataByPeriod(currentPeriod.servers);
    serversChart = new Chart(serversCtx, {
        type: 'line',
        data: {
            labels: serversData.labels,
            datasets: [{
                label: 'Servers Online',
                data: serversData.servers,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5,
                borderWidth: 2
            }]
        },
        options: chartOptions
    });
    
    // График ботов
    const botsCtx = document.getElementById('botsChart').getContext('2d');
    const botsData = filterDataByPeriod(currentPeriod.bots);
    botsChart = new Chart(botsCtx, {
        type: 'line',
        data: {
            labels: botsData.labels,
            datasets: [{
                label: 'Bots Active',
                data: botsData.bots,
                borderColor: '#764ba2',
                backgroundColor: 'rgba(118, 75, 162, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5,
                borderWidth: 2
            }]
        },
        options: chartOptions
    });
    
    // Обработчики кнопок времени
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const period = this.dataset.period;
            const chart = this.dataset.chart;
            
            this.parentElement.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            currentPeriod[chart] = period;
            updateChartData(chart, period);
        });
    });
}

// Обновление данных графика
function updateChartData(chartName, period) {
    const filtered = filterDataByPeriod(period);
    
    if (chartName === 'servers' && serversChart) {
        serversChart.data.labels = filtered.labels;
        serversChart.data.datasets[0].data = filtered.servers;
        serversChart.update('none');  // 'none' = без анимации
    } else if (chartName === 'bots' && botsChart) {
        botsChart.data.labels = filtered.labels;
        botsChart.data.datasets[0].data = filtered.bots;
        botsChart.update('none');  // 'none' = без анимации
    }
}

// Обновление цветов графиков
function updateChartColors() {
    if (!serversChart || !botsChart) return;
    
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#eaeaea' : '#333333';
    const gridColor = isDark ? '#2a2a4e' : '#e0e0e0';
    
    [serversChart, botsChart].forEach(chart => {
        chart.options.scales.y.ticks.color = textColor;
        chart.options.scales.y.grid.color = gridColor;
        chart.options.scales.x.ticks.color = textColor;
        chart.options.scales.x.grid.color = gridColor;
        chart.update('none');  // 'none' = без анимации
    });
}

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
    // Загружаем историю с backend
    await loadHistory();
    
    // Инициализируем графики
    initCharts();
    
    // Загружаем статистику
    loadStats();
    
    // Обновляем статистику каждые 5 секунд
    setInterval(loadStats, 5 * 1000);
    
    // Обновляем историю и графики каждые 5 секунд
    setInterval(async () => {
        await loadHistory();
        updateChartData('servers', currentPeriod.servers);
        updateChartData('bots', currentPeriod.bots);
    }, 5 * 1000);
});
