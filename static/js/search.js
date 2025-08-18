// 搜索功能
let searchIndex = [];
let searchInput;
let searchResults;

// 初始化搜索
document.addEventListener('DOMContentLoaded', function() {
    // 支持两种搜索框：导航栏搜索和搜索页面搜索
    searchInput = document.getElementById('search-input') || document.getElementById('searchInput');
    searchResults = document.getElementById('search-results') || document.getElementById('searchResults');
    
    if (searchInput && searchResults) {
        // 加载搜索索引
        fetch('/index.json')
            .then(response => response.json())
            .then(data => {
                searchIndex = data;
            })
            .catch(error => console.error('搜索索引加载失败:', error));
        
        // 搜索输入事件
        searchInput.addEventListener('input', handleSearch);
        
        // 点击外部关闭搜索结果
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
    }
});

// 处理搜索
function handleSearch(e) {
    const query = e.target.value.trim().toLowerCase();
    
    if (query.length < 2) {
        searchResults.style.display = 'none';
        return;
    }
    
    const results = searchIndex.filter(item => {
        return item.title.toLowerCase().includes(query) ||
               item.content.toLowerCase().includes(query) ||
               (item.tags && item.tags.some(tag => tag.toLowerCase().includes(query)));
    }).slice(0, 5); // 限制显示5个结果
    
    displaySearchResults(results, query);
}

// 显示搜索结果
function displaySearchResults(results, query) {
    if (results.length === 0) {
        if (searchResults.tagName === 'UL') {
            // PaperMod主题的搜索结果容器（ul）
            searchResults.innerHTML = '<li class="post-entry">未找到相关内容</li>';
        } else {
            // 自定义搜索结果容器（div）
            searchResults.innerHTML = '<div class="search-result-item">未找到相关内容</div>';
        }
        searchResults.style.display = 'block';
        return;
    }
    
    let html;
    if (searchResults.tagName === 'UL') {
        // PaperMod主题的搜索结果格式（ul > li）
        html = results.map(item => {
            const highlightedTitle = highlightText(item.title, query);
            return `<li class="post-entry"><header class="entry-header">${highlightedTitle}&nbsp;»</header><a href="${item.permalink}" aria-label="${item.title}"></a></li>`;
        }).join('');
    } else {
        // 自定义搜索结果格式（div）
        html = results.map(item => {
            const highlightedTitle = highlightText(item.title, query);
            const highlightedSummary = highlightText(item.summary || '', query);
            
            return `
                <div class="search-result-item" onclick="window.location.href='${item.permalink}'">
                    <h4>${highlightedTitle}</h4>
                    <p>${highlightedSummary}</p>
                    <small>${item.date}</small>
                </div>
            `;
        }).join('');
    }
    
    searchResults.innerHTML = html;
    searchResults.style.display = 'block';
}

// 高亮搜索关键词
function highlightText(text, query) {
    if (!text || !query) return text;
    
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

// 转义正则表达式特殊字符
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}