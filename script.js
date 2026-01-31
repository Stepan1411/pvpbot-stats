// URL бэкенда Railway
const BACKEND_URL = 'https://pvpbot-stats.up.railway.app/api/stats';
const FALLBACK_URL = 'data/stats.json';

// История данных для графиков (последние 24 часа)
let serversHistory = [];
let botsHistory = [];
let timeLabels = [];

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
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    
    // Добавляем новые данные
    timeLabels.push(timeStr);
    serversHistory.push(data.servers_online || 0);
    botsHistory.push(data.bots_active || 0);
    
    // Храним только последние 48 точек (24 часа при обновлении каждые 30 минут)
    if (timeLabels.length > 48) {
        timeLabels.shift();
        serversHistory.shift();
        botsHistory.shift();
    }
    
    // Обновляем графики
    updateCharts();
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
    serversChart = new Chart(serversCtx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: 'Servers Online',
                data: serversHistory,
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
    botsChart = new Chart(botsCtx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: 'Bots Active',
                data: botsHistory,
                borderColor: '#764ba2',
                backgroundColor: 'rgba(118, 75, 162, 0.1)',
                fill: true,
                tension: 0.4
            }]
        },
        options: chartOptions
    });
}

// Обновление графиков
function updateCharts() {
    if (serversChart && botsChart) {
        serversChart.data.labels = timeLabels;
        serversChart.data.datasets[0].data = serversHistory;
        serversChart.update();
        
        botsChart.data.labels = timeLabels;
        botsChart.data.datasets[0].data = botsHistory;
        botsChart.update();
    }
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
    initCharts();
    
    // Загружаем статистику сразу
    loadStats();
    
    // Обновляем статистику каждые 5 секунд для real-time эффекта
    setInterval(loadStats, 5 * 1000);
});
