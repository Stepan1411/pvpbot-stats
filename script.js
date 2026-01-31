// Загрузка статистики
async function loadStats() {
    try {
        const response = await fetch('data/stats.json');
        const data = await response.json();
        
        // Обновляем значения на странице
        document.getElementById('servers-online').textContent = data.servers_online || '0';
        document.getElementById('bots-active').textContent = data.bots_active || '0';
        document.getElementById('total-downloads').textContent = data.total_downloads || '0';
        document.getElementById('mod-version').textContent = data.mod_version || '1.0.0';
        
        // Обновляем время последнего обновления
        const lastUpdate = new Date(data.last_update);
        document.getElementById('last-update').textContent = lastUpdate.toLocaleString();
        
    } catch (error) {
        console.error('Failed to load stats:', error);
        document.getElementById('last-update').textContent = 'Failed to load';
    }
}

// Анимация чисел при загрузке
function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// Загружаем статистику при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    
    // Обновляем статистику каждые 5 минут
    setInterval(loadStats, 5 * 60 * 1000);
});

// Плавная прокрутка к секциям
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});
