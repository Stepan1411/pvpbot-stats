// URL бэкенда Railway
const BACKEND_URL = 'https://pvpbot-stats.up.railway.app/api/stats';
const FALLBACK_URL = 'data/stats.json';

// История данных для графиков
let historyData = {
    timestamps: [],
    servers: [],
    bots: []
};

// Текущий период отображения
let currentPeriod = {
    servers: '1h',
    bots: '1h'
};

// Графики
let serversChart = null;
let botsChart = null;

// Текущие значения для анимации
let currentValues = {
    servers: 0,
    bots: 0,
    spawned: 0,
    killed: 0
};

// Загрузка истории из localStorage
function loadHistory() {
    try {
        const saved = localStorage.getItem('statsHistory');
        if (saved) {
            historyData = JSON.parse(saved);
            // Очищаем старые данные (старше 1 года)
            const oneYearAgo = Date.now() - (365 * 24 * 60 * 60 * 1000);
            const validIndices = historyData.timestamps
                .map((ts, i) => ({ ts, i }))
                .filter(item => item.ts > oneYearAgo)
                .map(item => item.i);
            
            if (validIndices.length < historyData.timestamps.length) {
                historyData.timestamps = validIndices.map(i => historyData.timestamps[i]);
                historyData.servers = validIndices.map(i => historyData.servers[i]);
                historyData.bots = validIndices.map(i => historyData.bots[i]);
            }
        }
    } catch (e) {
        console.error('Failed to load history:', e);
    }
}

// Сохранение истории в localStorage
function saveHistory() {
    try {
        localStorage.setItem('statsHistory', JSON.stringify(historyData));
    } catch (e) {
        console.error('Failed to save history:', e);
    }
}

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

// Загрузка статистики
async function loadStats() {
    try {
        let response;
        try {
            response = await fetch(BACKEND_URL);
            if (!response.ok) throw new Error('Backend unavailable');
        } catch (backendError) {
            console.log('Backend unavailable, using fallback data');
            response = await fetch(FALLBACK_URL);
        }
        
        const data = await response.json();
        
        // Обновляем значения на странице с анимацией
        animateValue('servers-online', currentValues.servers, data.servers_online || 0);
        animateValue('bots-active', currentValues.bots, data.bots_active || 0);
        animateValue('bots-spawned', currentValues.spawned, data.bots_spawned_total || 0);
        animateValue('bots-killed', currentValues.killed, data.bots_killed_total || 0);
        
        // Сохраняем текущие значения
        currentValues.servers = data.servers_online || 0;
        currentValues.bots = data.bots_active || 0;
        currentValues.spawned = data.bots_spawned_total || 0;
        currentValues.killed = data.bots_killed_total || 0;
        
        // Обновляем время последнего обновления
        const lastUpdate = new Date(data.last_update);
        document.getElementById('last-update').textContent = lastUpdate.toLocaleString();
        
        // Добавляем данные в историю для графиков
        updateHistory(data);
        
    } catch (error) {
        console.error('Failed to load stats:', error);
        document.getElementById('last-update').textContent = 'Failed to load';
    }
}

// Анимация чисел
function animateValue(elementId, startValue, endValue) {
    const element = document.getElementById(elementId);
    
    // Если значения одинаковые - просто устанавливаем
    if (startValue === endValue) {
        element.textContent = endValue;
        return;
    }
    
    const duration = 500; // Быстрая анимация
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

// Обновление истории данных
function updateHistory(data) {
    const now = Date.now();
    
    // Добавляем новые данные
    historyData.timestamps.push(now);
    historyData.servers.push(data.servers_online || 0);
    historyData.bots.push(data.bots_active || 0);
    
    // Ограничиваем размер истории (максимум 10000 точек)
    if (historyData.timestamps.length > 10000) {
        historyData.timestamps.shift();
        historyData.servers.shift();
        historyData.bots.shift();
    }
    
    // Сохраняем в localStorage
    saveHistory();
    
    // Обновляем графики
    updateCharts();
}

// Фильтрация данных по периоду
function filterDataByPeriod(period) {
    const now = Date.now();
    let cutoff;
    
    switch(period) {
        case '1h':
            cutoff = now - (60 * 60 * 1000); // 1 час
            break;
        case '1d':
            cutoff = now - (24 * 60 * 60 * 1000); // 1 день
            break;
        case '1w':
            cutoff = now - (7 * 24 * 60 * 60 * 1000); // 1 неделя
            break;
        case '1m':
            cutoff = now - (30 * 24 * 60 * 60 * 1000); // 1 месяц
            break;
        case '1y':
            cutoff = now - (365 * 24 * 60 * 60 * 1000); // 1 год
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
    
    for (let i = 0; i < historyData.timestamps.length; i++) {
        if (historyData.timestamps[i] >= cutoff) {
            filtered.timestamps.push(historyData.timestamps[i]);
            filtered.servers.push(historyData.servers[i]);
            filtered.bots.push(historyData.bots[i]);
            
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
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    color: textColor,
                    precision: 0
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
                tension: 0.4
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
                tension: 0.4
            }]
        },
        options: chartOptions
    });
    
    // Обработчики кнопок периодов
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const period = this.dataset.period;
            const chart = this.dataset.chart;
            
            // Обновляем активную кнопку
            this.parentElement.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Обновляем период и график
            currentPeriod[chart] = period;
            updateChartData(chart, period);
        });
    });
}

// Обновление данных конкретного графика
function updateChartData(chartName, period) {
    const filtered = filterDataByPeriod(period);
    
    if (chartName === 'servers' && serversChart) {
        serversChart.data.labels = filtered.labels;
        serversChart.data.datasets[0].data = filtered.servers;
        serversChart.update();
    } else if (chartName === 'bots' && botsChart) {
        botsChart.data.labels = filtered.labels;
        botsChart.data.datasets[0].data = filtered.bots;
        botsChart.update();
    }
}

// Обновление графиков
function updateCharts() {
    updateChartData('servers', currentPeriod.servers);
    updateChartData('bots', currentPeriod.bots);
}

// Обновление цветов графиков при смене темы
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
        chart.update();
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Загружаем историю из localStorage
    loadHistory();
    
    // Инициализируем графики
    initCharts();
    
    // Загружаем статистику сразу
    loadStats();
    
    // Обновляем статистику каждые 5 секунд для real-time эффекта
    setInterval(loadStats, 5 * 1000);
});
