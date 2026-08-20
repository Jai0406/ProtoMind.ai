const API_BASE = "http://127.0.0.1:8000/api"; 

const DOM = {
    sidebar: document.getElementById('sidebar'),
    chatBox: document.getElementById('chat-box'),
    msgContainer: document.getElementById('message-container'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    greeting: document.getElementById('greeting'),
    modal: document.getElementById('abstract-modal'),
    modalTitle: document.getElementById('modal-title'),
    modalAbstract: document.getElementById('modal-abstract'),
    tabViews: document.querySelectorAll('.tab-view'),
    navBtns: document.querySelectorAll('.nav-btn')
};

const TOOL_MAPPINGS = {
    "fetch_tech_news": "Daily Tech Digest",
    "fetch_product_hunt_trending": "Product Radar",
    "fetch_arxiv_papers": "ArXiv Research Data",
    "search_arxiv_papers": "ArXiv Search Results",
    "fetch_github_trending": "Trending Repositories",
    "search_github_repos": "GitHub Search Results"
};

// --- STRICT BATCHING LIMITS ---
const TAB_LIMITS = {
    news:   { cap: Infinity, initial: 12, step: 6 },
    ph:     { cap: 10,       initial: 10, step: 10 }, 
    github: { cap: 15,       initial: 12, step: 3 },  
    arxiv:  { cap: 10,       initial: 10, step: 10 }  
};

function toolNameToType(toolName) {
    if (toolName === 'fetch_tech_news') return 'news';
    if (toolName === 'fetch_product_hunt_trending') return 'ph';
    if (toolName === 'fetch_arxiv_papers' || toolName === 'search_arxiv_papers') return 'arxiv';
    if (toolName === 'fetch_github_trending' || toolName === 'search_github_repos') return 'github';
    return 'news';
}

// --- DOMAINS FOR CHAT BUTTONS ---
const CHAT_GITHUB_DOMAINS = [
    { key: '1', name: 'AI & Machine Learning' }, { key: '2', name: 'Web Development' },
    { key: '3', name: 'Backend & API' }, { key: '4', name: 'Databases' },
    { key: '5', name: 'DevOps & Cloud' }, { key: '6', name: 'UI / UX Frameworks' }
];

const CHAT_ARXIV_DOMAINS = [
    { key: '1', name: 'Artificial Intelligence' }, { key: '2', name: 'Machine Learning' },
    { key: '3', name: 'Computer Vision' }, { key: '4', name: 'NLP' },
    { key: '5', name: 'Quantitative Finance' }, { key: '6', name: 'Cryptography & Security' }
];

const GITHUB_TRENDING_GENERIC_RE = /\b(trending|top|popular|latest)\b[\s\S]*\b(repo|repos|repositories|repository)\b|\bgithub\b[\s\S]*\b(trending|latest)\b/i;
const GITHUB_DOMAIN_HINT_RE = /\b(ai|machine learning|ml|web|frontend|backend|api|database|databases|devops|cloud|ui|ux)\b/i;

const ARXIV_GENERIC_RE = /\b(paper|papers|research|arxiv)\b/i;
const ARXIV_DOMAIN_HINT_RE = /\b(ai|machine learning|ml|vision|nlp|finance|crypto|security)\b/i;

function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function toggleSidebar() { DOM.sidebar.classList.toggle('collapsed'); }

function openAbstractModal(title, abstract) {
    DOM.modalTitle.innerText = title;
    DOM.modalAbstract.innerText = abstract;
    DOM.modal.style.display = 'flex';
    setTimeout(() => DOM.modal.classList.add('show'), 10);
}
function closeAbstractModal() {
    DOM.modal.classList.remove('show');
    setTimeout(() => DOM.modal.style.display = 'none', 300);
}

// --- TAB ROUTING ---
function selectDomain(val, title) {
    document.getElementById('github-mode').value = 'trending'; document.getElementById('github-category-select').value = val;
    document.getElementById('github-view-domains').style.display = 'none'; document.getElementById('github-view-data').style.display = 'block';
    document.getElementById('github-selected-title').innerText = title; fetchTabData('github', true); 
}
function selectGithubCurated(catKey, title) {
    document.getElementById('github-mode').value = 'curated'; document.getElementById('github-curated-select').value = catKey;
    document.getElementById('github-view-domains').style.display = 'none'; document.getElementById('github-view-data').style.display = 'block';
    document.getElementById('github-selected-title').innerText = `Industry Giants: ${title}`; fetchTabData('github', true);
}
function searchGithubRepos() {
    const keyword = document.getElementById('github-search-input').value.trim(); if (!keyword) return;
    document.getElementById('github-mode').value = 'search'; document.getElementById('github-search-keyword').value = keyword;
    document.getElementById('github-view-domains').style.display = 'none'; document.getElementById('github-view-data').style.display = 'block';
    document.getElementById('github-selected-title').innerText = `Search: "${keyword}"`; fetchTabData('github', true);
}
function showDomainGrid() {
    document.getElementById('github-view-data').style.display = 'none'; document.getElementById('github-view-domains').style.display = 'block';
    document.getElementById('github-category-select').value = ''; document.getElementById('github-curated-select').value = '';
    document.getElementById('github-search-keyword').value = ''; document.getElementById('github-mode').value = 'trending';
}
function selectArxivDomain(catKey, title) {
    document.getElementById('arxiv-mode').value = 'domain'; document.getElementById('arxiv-category-select').value = catKey;
    document.getElementById('arxiv-view-domains').style.display = 'none'; document.getElementById('arxiv-view-data').style.display = 'block';
    document.getElementById('arxiv-selected-title').innerText = title; fetchTabData('arxiv', true);
}
function searchArxivPapers() {
    const keyword = document.getElementById('arxiv-search-input').value.trim(); if (!keyword) return;
    document.getElementById('arxiv-mode').value = 'search'; document.getElementById('arxiv-search-keyword').value = keyword;
    document.getElementById('arxiv-view-domains').style.display = 'none'; document.getElementById('arxiv-view-data').style.display = 'block';
    document.getElementById('arxiv-selected-title').innerText = `Search: "${keyword}"`; fetchTabData('arxiv', true);
}
function showArxivDomainGrid() {
    document.getElementById('arxiv-view-data').style.display = 'none'; document.getElementById('arxiv-view-domains').style.display = 'block';
    document.getElementById('arxiv-category-select').value = ''; document.getElementById('arxiv-search-keyword').value = '';
}
function switchTab(tabId) {
    DOM.navBtns.forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`btn-${tabId}`);
    if (activeBtn) activeBtn.classList.add('active');

    DOM.tabViews.forEach(view => view.style.display = 'none');
    const activeView = document.getElementById(`view-${tabId}`);
    
    if (tabId === 'chat') { activeView.style.display = 'flex'; } 
    else if (tabId === 'github') { activeView.style.display = 'block'; showDomainGrid(); } 
    else if (tabId === 'arxiv') { activeView.style.display = 'block'; showArxivDomainGrid(); } 
    else { activeView.style.display = 'block'; fetchTabData(tabId); }
}

function handleEnter(e) { if (e.key === 'Enter') sendMessage(); }

// --- SUMMARIZATION API ---
async function requestSummary(title, content, url) {
    DOM.msgContainer.innerHTML += `<div class="msg user"><b>You:</b><br>Summarize this for me:<br><i>${title}</i></div>`;
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    try {
        const params = new URLSearchParams({ text: content, label: title });
        if (url && url !== '#') params.append('url', url);
        const response = await fetch(`${API_BASE}/summarize?${params.toString()}`, { method: 'POST' });
        if (!response.ok) throw new Error("Backend offline");
        const data = await response.json();
        const fallbackNote = data.is_fallback ? `<div style="color:#fbbf24; font-size:12px; margin-bottom:6px;">${data.header_label || 'AI summary unavailable — showing excerpt:'}</div>` : '';
        DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot"><b>ProtoMind Summary:</b><br>${fallbackNote}${data.content}</div>`);
    } catch (error) { DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot" style="color: #ef4444;"><b>Error generating summary.</b></div>`); }
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
}
async function requestRepoSummary(fullName) {
    DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg user"><b>You:</b><br>Summarize the README of:<br><i>${fullName}</i></div>`);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    try {
        const params = new URLSearchParams({ full_name: fullName });
        const response = await fetch(`${API_BASE}/github/readme?${params.toString()}`);
        if (!response.ok) throw new Error("Backend offline");
        const data = await response.json();
        const fallbackNote = data.is_fallback ? `<div style="color:#fbbf24; font-size:12px; margin-bottom:6px;">${data.header_label || 'AI summary unavailable — showing excerpt:'}</div>` : '';
        DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot"><b>ProtoMind Summary:</b><br>${fallbackNote}${data.content}</div>`);
    } catch (error) { DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot" style="color: #ef4444;"><b>Error fetching/generating README summary.</b></div>`); }
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
}

// --- DATA CACHING ---
window.chatBlockStore = {}; 
window.dataCache = { news: { data: [], showing: 0, fetchedAt: 0 }, ph: { data: [], showing: 0, fetchedAt: 0 }, github: {}, arxivDomain: {}, arxivSearch: {} };
const CACHE_MAX_AGE_MS = 10 * 60 * 1000; 

const TAB_CONFIG = {
    news: { gridId: 'news-grid', btnId: 'load-more-news' },
    ph: { gridId: 'ph-grid', btnId: null },
    github: { gridId: 'github-grid', btnId: 'load-more-github' },
    arxiv: { gridId: 'arxiv-grid', btnId: null }, 
};

function getGithubCacheEntry(cacheKeyName) {
    if (!window.dataCache.github[cacheKeyName]) window.dataCache.github[cacheKeyName] = { data: [], showing: 0, fetchedAt: 0 };
    return window.dataCache.github[cacheKeyName];
}
function getArxivDomainCacheEntry(categoryKey) {
    if (!window.dataCache.arxivDomain[categoryKey]) window.dataCache.arxivDomain[categoryKey] = { data: [], showing: 0, fetchedAt: 0 };
    return window.dataCache.arxivDomain[categoryKey];
}
function getArxivSearchCacheEntry(keyword) {
    const key = keyword.toLowerCase();
    if (!window.dataCache.arxivSearch[key]) window.dataCache.arxivSearch[key] = { data: [], showing: 0, fetchedAt: 0 };
    return window.dataCache.arxivSearch[key];
}
function isCacheFresh(entry) { return entry && entry.data && entry.data.length > 0 && (Date.now() - entry.fetchedAt) < CACHE_MAX_AGE_MS; }

// --- CHAT LOGIC ---
async function sendMessage() {
    const text = DOM.chatInput.value.trim();
    if (!text) return;

    DOM.greeting.style.display = 'none';
    DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg user"><b>You:</b><br>${text}</div>`);
    DOM.chatInput.value = '';
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;

    if (GITHUB_TRENDING_GENERIC_RE.test(text) && !GITHUB_DOMAIN_HINT_RE.test(text)) {
        DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot"><b>ProtoAI:</b><br>${renderDomainPromptChat("Select a domain to view trending repositories:", CHAT_GITHUB_DOMAINS, 'github')}</div>`);
        DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
        return;
    }

    if (ARXIV_GENERIC_RE.test(text) && !ARXIV_DOMAIN_HINT_RE.test(text) && !GITHUB_TRENDING_GENERIC_RE.test(text)) {
        DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot"><b>ProtoAI:</b><br>${renderDomainPromptChat("Select a domain to fetch the latest research papers:", CHAT_ARXIV_DOMAINS, 'arxiv')}</div>`);
        DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
        return;
    }

    DOM.sendBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/query`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_text: text }) });
        if (!response.ok) throw new Error("Backend offline");
        const data = await response.json();

        let botReply = "";
        if (data.type === "text") {
            botReply = (data.content || "").replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
        } else if (data.type === "tool_result") {
            botReply = initChatBlock(data.data, data.tool);
        }
        DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot"><b>ProtoAI:</b><br>${botReply}</div>`);
    } catch (error) {
        DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot" style="color: #ef4444;"><b>System Error:</b> Failed to connect to intelligence core. Is the API running?</div>`);
    }

    DOM.sendBtn.disabled = false;
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
}

function renderDomainPromptChat(message, domains, type) {
    const funcName = type === 'arxiv' ? 'selectArxivDomainInChat' : 'selectGithubDomainInChat';
    const buttonsHtml = domains.map(d =>
        `<button class="domain-option-btn-chat" onclick="${funcName}('${d.key}', '${escapeHtml(d.name).replace(/'/g, "\\'")}')">${escapeHtml(d.name)}</button>`
    ).join('');
    return `
    <div style="margin-bottom: 10px;">${message}</div>
    <div style="display: flex; flex-direction: column; gap: 10px; max-width: 450px;">
        ${buttonsHtml}
    </div>`;
}

async function selectGithubDomainInChat(key, name) {
    DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg user"><b>You:</b><br>Show trending repos: ${escapeHtml(name)}</div>`);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    const loadingId = 'load_' + Math.random().toString(36).substr(2, 9);
    DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot" id="${loadingId}"><b>ProtoAI:</b><br>Fetching trending repositories...</div>`);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    try {
        const res = await fetch(`${API_BASE}/github/trending?category_key=${encodeURIComponent(key)}&limit=1000`);
        if (!res.ok) throw new Error("Backend offline");
        const items = (await res.json()).items || [];
        document.getElementById(loadingId).innerHTML = `<b>ProtoAI:</b><br>${initChatBlock(items, 'fetch_github_trending')}`;
    } catch (error) { document.getElementById(loadingId).innerHTML = `<b>ProtoAI:</b><br><span style="color:#ef4444;">Error fetching repos.</span>`; }
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
}

async function selectArxivDomainInChat(key, name) {
    DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg user"><b>You:</b><br>Show research papers: ${escapeHtml(name)}</div>`);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    const loadingId = 'load_' + Math.random().toString(36).substr(2, 9);
    DOM.msgContainer.insertAdjacentHTML('beforeend', `<div class="msg bot" id="${loadingId}"><b>ProtoAI:</b><br>Fetching latest research papers...</div>`);
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
    try {
        const res = await fetch(`${API_BASE}/arxiv/latest?category_key=${encodeURIComponent(key)}&limit=1000&max_results=100`);
        if (!res.ok) throw new Error("Backend offline");
        const items = (await res.json()).items || [];
        document.getElementById(loadingId).innerHTML = `<b>ProtoAI:</b><br>${initChatBlock(items, 'fetch_arxiv_papers')}`;
    } catch (error) { document.getElementById(loadingId).innerHTML = `<b>ProtoAI:</b><br><span style="color:#ef4444;">Error fetching papers.</span>`; }
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
}

function initChatBlock(dataArray, toolName) {
    if (!Array.isArray(dataArray) || dataArray.length === 0) return "<p>No data found.</p>";

    const type = toolNameToType(toolName);
    const cap = TAB_LIMITS[type].cap;
    if (Number.isFinite(cap)) dataArray = dataArray.slice(0, cap);

    const blockId = 'cb_' + Math.random().toString(36).substr(2, 9);
    window.chatBlockStore[blockId] = { data: dataArray, showing: 0, total: dataArray.length, toolName: toolName, type: type };
    const friendlyName = TOOL_MAPPINGS[toolName] || "Retrieved Database Records";
    
    let html = `
    <div id="wrapper_${blockId}" style="width: 100%;">
        <b style="color: #94a3b8; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;">Source: ${friendlyName}</b><br>
        <div id="container_${blockId}" style="width: 100%;"></div>
        <div style="margin-top: 15px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 8px;">
            <div id="status_${blockId}" style="font-size: 12px; color: #64748b; display: none;"></div>
            <button id="btn_${blockId}" class="view-more-btn" style="display: none;" onclick="loadMoreChatItems('${blockId}')"></button>
        </div>
    </div>`;
    setTimeout(() => loadMoreChatItems(blockId), 50);
    return html;
}

function loadMoreChatItems(blockId) {
    const block = window.chatBlockStore[blockId];
    if (!block) return;
    const container = document.getElementById(`container_${blockId}`);
    const status = document.getElementById(`status_${blockId}`);
    const btn = document.getElementById(`btn_${blockId}`);
    
    const limits = TAB_LIMITS[block.type] || TAB_LIMITS.news;
    const batchSize = block.showing === 0 ? limits.initial : limits.step;
    const nextBatch = block.data.slice(block.showing, block.showing + batchSize);
    let newHtml = "";

    nextBatch.forEach(item => {
        if (block.toolName === "fetch_arxiv_papers" || block.toolName === "search_arxiv_papers") {
            const title = escapeHtml(item.title);
            const abstract = escapeHtml(item.abstract || "No abstract available.");
            const meta = `${escapeHtml(item.authors || 'Unknown')} • ${escapeHtml(item.date || '')}`;
            newHtml += `
            <div class="chat-horizontal-card">
                <div class="chat-hc-content">
                    <h4>${title}</h4><div class="chat-hc-meta">${meta}</div><div class="chat-hc-desc">${abstract}</div>
                </div>
                <div class="chat-hc-actions">
                    <button class="chat-hc-btn" onclick="requestSummary('${title.replace(/'/g, "\\'")}', '${abstract.replace(/'/g, "\\'")}', '${item.pdf_url || '#'}')">Summarize</button>
                    <a href="${item.page_url || '#'}" target="_blank" class="chat-hc-btn view">Page</a>
                    <a href="${item.pdf_url || '#'}" target="_blank" class="chat-hc-btn view">PDF</a>
                </div>
            </div>`;
            return; 
        }

        let title, desc, meta, link, summarizeFn;
        if (block.toolName === "fetch_github_trending" || block.toolName === "search_github_repos") {
            title = item.full_name || item.name;
            desc = item.description || "No description provided.";
            meta = `Stars: ${new Intl.NumberFormat().format(item.stars || 0)} | Lang: ${item.language || 'N/A'}`;
            link = item.html_url || "#";
            summarizeFn = `requestRepoSummary('${escapeHtml(title).replace(/'/g, "\\'")}')`;
        } else {
            title = item.title || item.product_name || item.full_name || item.name || "Unknown";
            desc = item.description || item.tagline || item.abstract || "No description provided.";
            meta = item.source || item.category || item.date || item.publishedAt || item.language || "";
            link = item.url || item.ph_post_link || item.ph_link || item.html_url || item.pdf_url || "#";
            summarizeFn = `requestSummary('${escapeHtml(title).replace(/'/g, "\\'")}', '${escapeHtml(desc).replace(/'/g, "\\'")}', '${link}')`;
        }

        newHtml += `
        <div class="chat-horizontal-card">
            <div class="chat-hc-content">
                <h4>${escapeHtml(title)}</h4><div class="chat-hc-meta">${escapeHtml(meta)}</div><div class="chat-hc-desc">${escapeHtml(desc)}</div>
            </div>
            <div class="chat-hc-actions">
                <button class="chat-hc-btn" onclick="${summarizeFn}">Summarize</button>
                <a href="${link}" target="_blank" class="chat-hc-btn view">View Link</a>
            </div>
        </div>`;
    });

    container.insertAdjacentHTML('beforeend', newHtml);
    block.showing += nextBatch.length;
    
    if (block.showing >= block.total) { 
        if (btn) btn.style.setProperty('display', 'none', 'important'); 
        if (status) status.style.setProperty('display', 'none', 'important');
    } else {
        if (btn) {
            btn.style.setProperty('display', 'block', 'important');
            btn.innerText = `Load More Results (${block.total - block.showing} remaining)`;
        }
    }
    DOM.chatBox.scrollTop = DOM.chatBox.scrollHeight;
}

// --- FETCHING TAB DATA ---
async function fetchTabData(tabType, forceRefresh = false) {
    let entry, apiPath;
    if (tabType === 'github') {
        const mode = document.getElementById('github-mode').value;
        if (mode === 'search') {
            const keyword = document.getElementById('github-search-keyword').value;
            entry = getGithubCacheEntry(`search_${keyword}`); 
            apiPath = `/github/search?keyword=${encodeURIComponent(keyword)}&limit=1000`;
        } else if (mode === 'curated') {
            const catKey = document.getElementById('github-curated-select').value;
            entry = getGithubCacheEntry(`curated_${catKey}`); 
            apiPath = `/github/curated?category_key=${catKey}&limit=1000`;
        } else {
            const catKey = document.getElementById('github-category-select').value;
            entry = getGithubCacheEntry(`trending_${catKey}`); 
            apiPath = `/github/trending?category_key=${catKey}&limit=1000`;
        }
    } else if (tabType === 'arxiv') {
        const mode = document.getElementById('arxiv-mode').value;
        if (mode === 'search') {
            const keyword = document.getElementById('arxiv-search-keyword').value;
            entry = getArxivSearchCacheEntry(keyword); apiPath = `/arxiv/search?keyword=${encodeURIComponent(keyword)}&limit=1000&max_results=100`;
        } else {
            const catKey = document.getElementById('arxiv-category-select').value;
            entry = getArxivDomainCacheEntry(catKey); apiPath = `/arxiv/latest?category_key=${catKey}&limit=1000&max_results=100`;
        }
    } else {
        entry = window.dataCache[tabType];
        apiPath = tabType === 'news' ? '/news?limit=1000' : '/products?limit=1000';
    }

    const { gridId, btnId } = TAB_CONFIG[tabType];
    const grid = document.getElementById(gridId);
    const loadBtn = btnId ? document.getElementById(btnId) : null;

    document.getElementById(`loading-${tabType}`).style.display = 'flex';
    document.getElementById(`content-${tabType}`).style.display = 'none';

    // FORCE HIDE during load to overwrite CSS !important rule
    if (loadBtn) { loadBtn.style.setProperty('display', 'none', 'important'); }

    await new Promise(resolve => setTimeout(resolve, 1500)); 

    if (!forceRefresh && isCacheFresh(entry)) {
        grid.innerHTML = ''; entry.showing = 0; 
        loadMoreTabItems(tabType);
        document.getElementById(`loading-${tabType}`).style.display = 'none'; 
        document.getElementById(`content-${tabType}`).style.display = 'block'; 
        return;
    }

    grid.innerHTML = ''; 

    try {
        const res = await fetch(`${API_BASE}${apiPath}`);
        if (!res.ok) throw new Error("Network error");
        let fetchedItems = (await res.json()).items || []; 

        const capLimit = (TAB_LIMITS[tabType] || TAB_LIMITS.news).cap;
        if (Number.isFinite(capLimit)) fetchedItems = fetchedItems.slice(0, capLimit);

        entry.data = fetchedItems;
        entry.showing = 0; 
        entry.fetchedAt = Date.now();
        loadMoreTabItems(tabType);
        
        document.getElementById(`loading-${tabType}`).style.display = 'none'; 
        document.getElementById(`content-${tabType}`).style.display = 'block';
    } catch (err) {
        document.getElementById(`loading-${tabType}`).style.display = 'none';
        document.getElementById(`content-${tabType}`).style.display = 'block';
        if (loadBtn) {
            loadBtn.style.setProperty('display', 'block', 'important');
            loadBtn.innerText = "Connection failed — click here to retry"; 
            loadBtn.disabled = false; 
            loadBtn.onclick = () => fetchTabData(tabType, true);
        }
    }
}

function loadMoreTabItems(tabType) {
    let store;
    if (tabType === 'github') { 
        const mode = document.getElementById('github-mode').value;
        if (mode === 'search') { store = getGithubCacheEntry(`search_${document.getElementById('github-search-keyword').value}`); } 
        else if (mode === 'curated') { store = getGithubCacheEntry(`curated_${document.getElementById('github-curated-select').value}`); } 
        else { store = getGithubCacheEntry(`trending_${document.getElementById('github-category-select').value}`); }
    } else if (tabType === 'arxiv') {
        store = document.getElementById('arxiv-mode').value === 'search' ? getArxivSearchCacheEntry(document.getElementById('arxiv-search-keyword').value) : getArxivDomainCacheEntry(document.getElementById('arxiv-category-select').value);
    } else { store = window.dataCache[tabType]; }

    const { gridId, btnId } = TAB_CONFIG[tabType];
    const grid = document.getElementById(gridId); 
    const btn = btnId ? document.getElementById(btnId) : null;
    
    const limits = TAB_LIMITS[tabType] || TAB_LIMITS.news;
    const batchSize = store.showing === 0 ? limits.initial : limits.step;
    const nextBatch = store.data.slice(store.showing, store.showing + batchSize);
    let batchHtml = "";

    nextBatch.forEach(item => {
        if (tabType === 'news') {
            batchHtml += `
                <div class="card" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
                    <div style="flex-grow: 1;">
                        <h3 style="margin-bottom: 8px;">${escapeHtml(item.title)}</h3>
                        <div class="meta" style="margin-bottom: 12px;">${escapeHtml(item.source)} • ${escapeHtml(item.date || item.publishedAt)}</div>
                        <div style="font-size: 14px; color: #cbd5e1; display: -webkit-box; -webkit-line-clamp: 3; line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 15px;">${escapeHtml(item.description || "No description available.")}</div>
                    </div>
                    <div class="action-row"><a href="${item.url}" target="_blank" class="read-btn">Read Full Article</a></div>
                </div>`;
        } else if (tabType === 'ph') {
            batchHtml += `
                <div class="card" style="flex-direction: row; justify-content: space-between; align-items: center;">
                    <div style="flex-grow: 1;">
                        <h3 style="margin-bottom: 8px;">${escapeHtml(item.name)}</h3>
                        <div class="meta" style="color: #cbd5e1; margin-bottom: 8px;">${escapeHtml(item.tagline)}</div>
                        <div class="meta">Category: ${escapeHtml(item.category)}</div>
                    </div>
                    <div style="text-align: right; min-width: 120px; display: flex; flex-direction: column; align-items: flex-end; justify-content: center;">
                        <div style="color: #34d399; font-weight: 700; font-size: 15px; margin-bottom: 12px; background: rgba(52, 211, 153, 0.1); padding: 6px 14px; border-radius: 20px;">▲ ${new Intl.NumberFormat().format(item.votes || 0)}</div>
                        <a href="${item.ph_link}" target="_blank" class="read-btn" style="border: 1px solid #334155; padding: 6px 15px; border-radius: 8px;">View Product</a>
                    </div>
                </div>`;
        } else if (tabType === 'github') {
            batchHtml += `
                <div class="card" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
                    <div style="flex-grow: 1;">
                        <h3 style="margin-bottom: 12px; font-size: 17px; color: #60a5fa;">${escapeHtml(item.full_name || item.name)}</h3>
                        <div class="meta" style="color: #cbd5e1; margin-bottom: 20px; line-height: 1.6;">${escapeHtml(item.description || "No description provided.")}</div>
                        <div style="margin-bottom: 15px; display: flex; flex-wrap: wrap; gap: 8px;">
                            <span class="chip warning">★ ${new Intl.NumberFormat().format(item.stars || 0)} Stars</span>
                            <span class="chip neutral">⑂ ${new Intl.NumberFormat().format(item.forks || 0)} Forks</span>
                            <span class="chip positive">&lt;/&gt; ${escapeHtml(item.language || "N/A")}</span>
                        </div>
                    </div>
                    <div class="action-row"><a href="${item.html_url || '#'}" target="_blank" class="read-btn">Inspect Repository</a></div>
                </div>`;
        } else if (tabType === 'arxiv') {
            const title = escapeHtml(item.title);
            const abstract = escapeHtml(item.abstract || "No abstract available.");
            
            batchHtml += `
                <div class="card" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
                    <div style="flex-grow: 1;">
                        <h3 style="margin-bottom: 8px;">${title}</h3>
                        <div class="meta">${escapeHtml(item.authors || 'Unknown')} • ${escapeHtml(item.date || '')}</div>
                    </div>
                    <div class="action-row" style="display: flex; justify-content: space-between; align-items: center; margin-top: auto; padding-top: 15px; border-top: 1px solid #1e293b;">
                        <button class="read-btn" style="padding: 0; background: transparent; border: none; cursor: pointer; font-size: 14px; text-align: left;" onclick="openAbstractModal('${title.replace(/'/g, "\\'")}', '${abstract.replace(/'/g, "\\'")}')">View Abstract</button>
                        <div style="display: flex; gap: 15px;">
                            <a href="${item.page_url || '#'}" target="_blank" class="read-btn">ArXiv Page</a>
                            <a href="${item.pdf_url || '#'}" target="_blank" class="read-btn">Download PDF</a>
                        </div>
                    </div>
                </div>`;
        }
    });

    grid.insertAdjacentHTML('beforeend', batchHtml);
    store.showing += nextBatch.length;

    // FORCE HIDE with !important overriding CSS
    if (btn) {
        if (store.showing >= store.data.length) { 
            btn.style.setProperty('display', 'none', 'important'); 
        } else {
            btn.style.setProperty('display', 'block', 'important'); 
            btn.disabled = false; 
            btn.innerText = `Load More Intelligence (${store.data.length - store.showing} remaining)`; 
            btn.onclick = () => loadMoreTabItems(tabType);
        }
    }
}

// --- SMOOTH APP BOOT SEQUENCE ---
window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const loader = document.getElementById('app-boot-loader');
        if (loader) {
            loader.style.opacity = '0';
            loader.style.visibility = 'hidden';
            setTimeout(() => loader.remove(), 800);
        }
    }, 4500); 
});