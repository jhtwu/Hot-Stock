// API 基礎 URL
const API_BASE = '';

// 当前选择的日期
let currentDate = null;

// 頁面加載完成後初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    setupEventListeners();
    loadAvailableDates();
    loadRankings();
    handleStockDeepLink();
});

// 初始化頁面
function initializePage() {
    console.log('Hot Stock Analysis Platform Initialized');
}

// 設置事件監聽器
function setupEventListeners() {
    // 標籤頁切換
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });

    // 日期選擇
    document.getElementById('dateSelect').addEventListener('change', function() {
        currentDate = this.value;
        loadRankings();
    });

    // 重新整理
    document.getElementById('refreshBtn').addEventListener('click', function() {
        loadRankings();
    });

    // 立即分析
    document.getElementById('runAnalysisBtn').addEventListener('click', function() {
        runAnalysis();
    });

    // 模態框關閉
    document.querySelector('.close').addEventListener('click', function() {
        document.getElementById('stockModal').style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        const modal = document.getElementById('stockModal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// 切換標籤頁
function switchTab(tabName) {
    // 更新按鈕狀態
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // 更新內容顯示
    document.querySelectorAll('.ranking-list').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-content`).classList.add('active');
}

// 加載可用日期
async function loadAvailableDates() {
    try {
        const response = await fetch(`${API_BASE}/api/dates`);
        const data = await response.json();

        const select = document.getElementById('dateSelect');
        select.innerHTML = '<option value="">最新数据</option>';

        data.dates.forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.textContent = date;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('載入日期列表失敗:', error);
    }
}

// 加載榜單資料
async function loadRankings() {
    try {
        const url = currentDate
            ? `${API_BASE}/api/rankings?date=${currentDate}`
            : `${API_BASE}/api/rankings`;

        const response = await fetch(url);
        const data = await response.json();

        // 更新统计信息
        updateStatistics(data);

        // 更新各个榜单
        updateHotRanking(data.rankings.hot);
        updateGrowthRanking(data.rankings.growth);
        updateDiscussionRanking(data.rankings.discussion);
        updateActiveRanking(data.rankings.active);

    } catch (error) {
        console.error('載入榜單資料失敗:', error);
        showError('無法載入資料，請稍後重試');
    }
}

// 更新統計資訊
function updateStatistics(data) {
    const allStocks = [
        ...data.rankings.hot,
        ...data.rankings.growth,
        ...data.rankings.discussion,
        ...data.rankings.active
    ];

    // 去重
    const uniqueSymbols = new Set(allStocks.map(s => s.symbol));
    document.getElementById('totalStocks').textContent = uniqueSymbols.size;

    // 平均分數
    const avgScore = allStocks.reduce((sum, s) => sum + s.total_score, 0) / allStocks.length;
    document.getElementById('avgScore').textContent = avgScore.toFixed(1);

    // 總新聞數
    const totalNews = allStocks.reduce((sum, s) => sum + s.news_count, 0);
    document.getElementById('totalNews').textContent = totalNews;

    // 更新時間
    document.getElementById('updateTime').textContent = data.date;
}

// 更新熱度榜
function updateHotRanking(stocks) {
    const tbody = document.getElementById('hotTableBody');
    tbody.innerHTML = '';

    stocks.forEach((stock, index) => {
        const row = createTableRow([
            createRankCell(index + 1),
            createSymbolCell(stock.symbol),
            stock.name,
            stock.sector || '-',
            stock.total_score.toFixed(2),
            createChangeCell(stock.price_change),
            stock.news_count,
            createActionCell(stock.symbol)
        ]);
        tbody.appendChild(row);
    });
}

// 更新漲幅榜
function updateGrowthRanking(stocks) {
    const tbody = document.getElementById('growthTableBody');
    tbody.innerHTML = '';

    stocks.forEach((stock, index) => {
        const row = createTableRow([
            createRankCell(index + 1),
            createSymbolCell(stock.symbol),
            stock.name,
            stock.sector || '-',
            createChangeCell(stock.price_change),
            stock.volume_ratio.toFixed(2) + 'x',
            stock.total_score.toFixed(2),
            createActionCell(stock.symbol)
        ]);
        tbody.appendChild(row);
    });
}

// 更新討論榜
function updateDiscussionRanking(stocks) {
    const tbody = document.getElementById('discussionTableBody');
    tbody.innerHTML = '';

    stocks.forEach((stock, index) => {
        const sentiment = stock.news_sentiment_score || 0;
        const row = createTableRow([
            createRankCell(index + 1),
            createSymbolCell(stock.symbol),
            stock.name,
            stock.sector || '-',
            stock.news_count,
            createSentimentCell(sentiment),
            stock.total_score.toFixed(2),
            createActionCell(stock.symbol)
        ]);
        tbody.appendChild(row);
    });
}

// 更新活躍榜
function updateActiveRanking(stocks) {
    const tbody = document.getElementById('activeTableBody');
    tbody.innerHTML = '';

    stocks.forEach((stock, index) => {
        const row = createTableRow([
            createRankCell(index + 1),
            createSymbolCell(stock.symbol),
            stock.name,
            stock.sector || '-',
            stock.volume_ratio.toFixed(2) + 'x',
            createChangeCell(stock.price_change),
            stock.total_score.toFixed(2),
            createActionCell(stock.symbol)
        ]);
        tbody.appendChild(row);
    });
}

// 建立表格列
function createTableRow(cells) {
    const row = document.createElement('tr');
    cells.forEach(cell => {
        const td = document.createElement('td');
        // 既支持 DOM 节点也支持基础类型
        if (cell instanceof Node) {
            td.appendChild(cell);
        } else {
            td.textContent = cell !== undefined && cell !== null ? cell : '-';
        }
        row.appendChild(td);
    });
    return row;
}

// 建立排名欄位
function createRankCell(rank) {
    const span = document.createElement('span');
    span.className = `rank rank-${rank <= 3 ? rank : ''}`;
    span.textContent = rank;
    return span;
}

// 建立股票代碼欄位
function createSymbolCell(symbol) {
    const link = document.createElement('a');
    link.className = 'symbol';
    link.textContent = symbol;
    link.href = `/stock/${symbol}`;
    link.onclick = (e) => {
        e.preventDefault();
        window.history.pushState({}, '', link.href);
        showStockDetail(symbol);
    };
    return link;
}

// 建立漲跌幅欄位
function createChangeCell(change) {
    const span = document.createElement('span');
    const value = parseFloat(change);

    if (value > 0) {
        span.className = 'positive';
        span.textContent = `+${value.toFixed(2)}%`;
    } else if (value < 0) {
        span.className = 'negative';
        span.textContent = `${value.toFixed(2)}%`;
    } else {
        span.className = 'neutral';
        span.textContent = '0.00%';
    }

    return span;
}

// 建立情緒分數欄位
function createSentimentCell(score) {
    const span = document.createElement('span');
    const value = parseFloat(score);

    if (value > 60) {
        span.className = 'positive';
        span.textContent = value.toFixed(1);
    } else if (value < 40) {
        span.className = 'negative';
        span.textContent = value.toFixed(1);
    } else {
        span.className = 'neutral';
        span.textContent = value.toFixed(1);
    }

    return span;
}

// 建立操作按鈕
function createActionCell(symbol) {
    const btn = document.createElement('button');
    btn.className = 'detail-btn';
    btn.textContent = '查看詳情';
    btn.onclick = () => showStockDetail(symbol);
    return btn;
}

// 顯示股票詳情
async function showStockDetail(symbol) {
    const modal = document.getElementById('stockModal');
    const title = document.getElementById('stockTitle');
    const info = document.getElementById('stockInfo');

    title.textContent = '載入中...';
    info.innerHTML = '<p>正在載入股票詳情...</p>';
    modal.style.display = 'block';

    try {
        const response = await fetch(`${API_BASE}/api/stock/${symbol}`);
        const data = await response.json();

        title.textContent = `${data.symbol} - ${data.name}`;

        let html = `
            <div style="margin-bottom: 20px;">
                <h3>基本信息</h3>
                <p><strong>板塊:</strong> ${data.sector}</p>
            </div>
        `;

        if (data.latest_score) {
            html += `
                <div style="margin-bottom: 20px;">
                    <h3>最新評分</h3>
                    <p><strong>綜合評分:</strong> ${data.latest_score.total_score.toFixed(2)}</p>
                    <p><strong>熱度排名:</strong> ${data.latest_score.hot_rank || '-'}</p>
                    <p><strong>漲幅排名:</strong> ${data.latest_score.growth_rank || '-'}</p>
                    <p><strong>價格變化:</strong> <span class="${data.latest_score.price_change > 0 ? 'positive' : 'negative'}">${data.latest_score.price_change > 0 ? '+' : ''}${data.latest_score.price_change.toFixed(2)}%</span></p>
                    <p><strong>新聞數量:</strong> ${data.latest_score.news_count}</p>
                </div>
            `;
        }

        if (data.recent_news && data.recent_news.length > 0) {
            html += `
                <div style="margin-bottom: 20px;">
                    <h3>最新新聞</h3>
                    <ul style="list-style: none; padding: 0;">
            `;
            data.recent_news.slice(0, 5).forEach(news => {
                html += `
                    <li style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                        <strong>${news.title}</strong><br>
                        <small>來源: ${news.source} | ${news.published_at}</small><br>
                        <a href="${news.url}" target="_blank" style="color: #667eea;">閱讀原文 →</a>
                    </li>
                `;
            });
            html += `</ul></div>`;
        }

        info.innerHTML = html;

    } catch (error) {
        console.error('加载股票详情失败:', error);
        info.innerHTML = '<p style="color: red;">載入失敗，請稍後重試</p>';
    }
}

// 運行分析任務
async function runAnalysis() {
    const btn = document.getElementById('runAnalysisBtn');
    btn.disabled = true;
    btn.textContent = '分析中...';

    try {
        const response = await fetch(`${API_BASE}/api/run-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            alert(data.message + '\n\n注意：首次執行需要下載資料，可能需要較長時間。');

            // 10 秒后自动刷新页面
            setTimeout(() => {
                loadRankings();
            }, 10000);
        } else {
            throw new Error('分析任务启动失败');
        }

    } catch (error) {
        console.error('運行分析失敗:', error);
        alert('運行分析失敗，請檢查後端服務是否正常運行。\n\n錯誤資訊：' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '立即分析';
    }
}

// 顯示錯誤信息
function showError(message) {
    const tbody = document.querySelectorAll('tbody');
    tbody.forEach(tb => {
        tb.innerHTML = `<tr><td colspan="8" class="loading" style="color: red;">${message}</td></tr>`;
    });
}

// 支援 /stock/{symbol} 深鏈接
function handleStockDeepLink() {
    const path = window.location.pathname;
    const match = path.match(/^\\/stock\\/([A-Za-z\\.\\-]+)$/);
    if (match) {
        const symbol = match[1].toUpperCase();
        showStockDetail(symbol);
    }
}
