/* ============================================
   BEU Result AI — Frontend Logic
   ============================================ */

const API_BASE = '';

// DOM refs
const layoutWrapper = document.getElementById('layout-wrapper');
const inputSection = document.getElementById('input-section');
const loadingSection = document.getElementById('loading-section');
const errorSection = document.getElementById('error-section');
const resultsSection = document.getElementById('results-section');

const form = document.getElementById('result-form');
const regInput = document.getElementById('reg-no');
const semesterInput = document.getElementById('semester');
const submitBtn = document.getElementById('submit-btn');
const semGrid = document.getElementById('semester-grid');
const retryBtn = document.getElementById('retry-btn');
const checkAnotherBtn = document.getElementById('check-another-btn');

// Chat refs
const chatSidebar = document.getElementById('chat-sidebar');
const chatFab = document.getElementById('chat-fab');
const chatCloseBtn = document.getElementById('chat-close-btn');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send-btn');
const chatSuggestions = document.getElementById('chat-suggestions');

let subjectChart = null;
let currentResultData = null; // store for chat context

// Center layout when chat is hidden
layoutWrapper.classList.add('centered');

// ==========================================
// Semester Selection
// ==========================================

semGrid.addEventListener('click', (e) => {
    const btn = e.target.closest('.sem-btn');
    if (!btn) return;
    document.querySelectorAll('.sem-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    semesterInput.value = btn.dataset.sem;
});

// ==========================================
// Form Submit
// ==========================================

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const regNo = regInput.value.trim();
    const semester = parseInt(semesterInput.value);
    if (!regNo || !semester) { shakeElement(submitBtn); return; }
    await fetchAndAnalyze(regNo, semester);
});

retryBtn.addEventListener('click', () => {
    showSection('input');
    layoutWrapper.classList.add('centered');
});

checkAnotherBtn.addEventListener('click', () => {
    regInput.value = '';
    semesterInput.value = '';
    document.querySelectorAll('.sem-btn').forEach(b => b.classList.remove('active'));
    currentResultData = null;
    chatSidebar.classList.add('hidden');
    chatFab.classList.add('hidden');
    layoutWrapper.classList.add('centered');
    showSection('input');
});

// ==========================================
// Chat Toggle
// ==========================================

chatFab.addEventListener('click', () => {
    chatSidebar.classList.remove('hidden');
    chatFab.classList.add('hidden');
    layoutWrapper.classList.remove('centered');
    chatInput.focus();
});

chatCloseBtn.addEventListener('click', () => {
    chatSidebar.classList.add('hidden');
    chatFab.classList.remove('hidden');
    layoutWrapper.classList.add('centered');
});

// Chat send
chatSendBtn.addEventListener('click', () => sendChatMessage());
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
});

// Suggestion chips
chatSuggestions.addEventListener('click', (e) => {
    const chip = e.target.closest('.suggestion-chip');
    if (!chip) return;
    chatInput.value = chip.dataset.msg;
    sendChatMessage();
});

async function sendChatMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    // Add user message
    appendChatMsg(msg, 'user');
    chatInput.value = '';
    chatSendBtn.disabled = true;

    // Show typing indicator
    const typingEl = appendChatMsg('Thinking…', 'ai typing');

    try {
        const res = await fetch(`${API_BASE}/result/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, context: currentResultData }),
        });
        const data = await res.json();
        typingEl.remove();
        appendChatMsg(data.reply || 'Sorry, no response.', 'ai');
    } catch (err) {
        typingEl.remove();
        appendChatMsg('Failed to get a response. Please try again.', 'ai');
    }

    chatSendBtn.disabled = false;
    chatInput.focus();
}

function appendChatMsg(text, cls) {
    // Remove welcome if first real message
    const welcome = chatMessages.querySelector('.chat-welcome');
    if (welcome && !cls.includes('typing')) welcome.remove();

    const div = document.createElement('div');
    div.className = `chat-msg ${cls}`;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
}

// ==========================================
// API Call
// ==========================================

async function fetchAndAnalyze(regNo, semester) {
    showSection('loading');
    updateLoadingStep('fetch');

    try {
        await sleep(400);
        updateLoadingStep('analyze');

        const response = await fetch(`${API_BASE}/result/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reg_no: regNo, semester: semester }),
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);
        const data = await response.json();

        updateLoadingStep('explain');
        await sleep(300);

        if (!data.success) { showError(data.error || 'Unknown error'); return; }

        currentResultData = data;
        renderResults(data);
        showSection('results');
        chatFab.classList.remove('hidden');
    } catch (err) {
        showError(err.message || 'Failed to connect to the server.');
    }
}

// ==========================================
// Section Visibility
// ==========================================

function showSection(section) {
    inputSection.classList.toggle('hidden', section !== 'input');
    loadingSection.classList.toggle('hidden', section !== 'loading');
    errorSection.classList.toggle('hidden', section !== 'error');
    resultsSection.classList.toggle('hidden', section !== 'results');
    if (section === 'results') window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showError(message) {
    document.getElementById('error-message').textContent = message;
    showSection('error');
}

function updateLoadingStep(step) {
    const steps = ['fetch', 'analyze', 'explain'];
    const idx = steps.indexOf(step);
    steps.forEach((s, i) => {
        const el = document.getElementById(`step-${s}`);
        el.classList.remove('active', 'done');
        if (i < idx) el.classList.add('done');
        if (i === idx) el.classList.add('active');
    });
    const titles = {
        fetch: ['Fetching your result…', 'Connecting to BEU servers'],
        analyze: ['Analyzing your performance…', 'AI is crunching the numbers'],
        explain: ['Generating your report…', 'Almost there'],
    };
    document.getElementById('loading-title').textContent = titles[step][0];
    document.getElementById('loading-desc').textContent = titles[step][1];
}

// ==========================================
// Render Results
// ==========================================

function renderResults(data) {
    const name = data.student_name || 'Student';
    document.getElementById('student-avatar').textContent = name.charAt(0).toUpperCase();
    document.getElementById('student-name').textContent = titleCase(name);
    document.getElementById('student-meta').textContent = `Reg: ${data.reg_no} · Semester ${data.semester}`;
    document.getElementById('student-college').textContent = data.college_name ? titleCase(data.college_name) : '';

    const badge = document.getElementById('status-badge');
    const status = (data.overall_status || 'PASS').toUpperCase();
    badge.textContent = status;
    badge.className = 'status-badge ' + (status === 'PASS' ? 'pass' : status === 'FAIL' ? 'fail' : 'backlog');

    setMetric('val-percentage', data.percentage, v => v.toFixed(1) + '%', percentageColor);
    setMetric('val-sgpa', data.sgpa, v => v.toFixed(1), () => 'text-indigo');
    setMetric('val-cgpa', data.cgpa, v => v.toFixed(1), () => 'text-violet');

    const perfEl = document.getElementById('val-performance');
    perfEl.textContent = data.performance_level || '—';
    perfEl.className = 'metric-value ' + performanceColor(data.performance_level);

    // AI Explanation as bullet points
    renderExplanationBullets(data.explanation || '');

    renderSubjects(data.subjects || []);
    renderList('strength-list', data.strength_subjects);
    renderList('weakness-list', data.weak_subjects);
    renderTips(data.study_tips || []);
}

function setMetric(id, val, fmt, colorFn) {
    const el = document.getElementById(id);
    el.textContent = val != null ? fmt(val) : '—';
    el.className = 'metric-value ' + (val != null ? colorFn(val) : '');
}

function renderExplanationBullets(text) {
    const ul = document.getElementById('explanation-bullets');
    ul.innerHTML = '';

    // Split by bullet markers or newlines
    let lines = text.split(/[•\n]/).map(l => l.trim()).filter(l => l.length > 0);

    // If no bullets found, split by sentences
    if (lines.length <= 1 && text.length > 0) {
        lines = text.match(/[^.!?]+[.!?]+/g) || [text];
        lines = lines.map(l => l.trim()).filter(l => l.length > 5);
    }

    lines.forEach(line => {
        const li = document.createElement('li');
        li.textContent = line;
        ul.appendChild(li);
    });
}

function renderList(id, items) {
    const ul = document.getElementById(id);
    ul.innerHTML = '';
    (items || []).forEach(s => {
        const li = document.createElement('li');
        li.textContent = s;
        ul.appendChild(li);
    });
    if (ul.children.length === 0) {
        ul.innerHTML = '<li style="color: var(--text-muted);">None identified</li>';
    }
}

function renderTips(tips) {
    const grid = document.getElementById('tips-grid');
    grid.innerHTML = '';
    tips.forEach((tip, i) => {
        const div = document.createElement('div');
        div.className = 'tip-item';
        div.innerHTML = `<div class="tip-number">${i + 1}</div><span>${tip}</span>`;
        grid.appendChild(div);
    });
}

// ==========================================
// Subjects
// ==========================================

function renderSubjects(subjects) {
    const tbody = document.getElementById('subjects-tbody');
    tbody.innerHTML = '';
    subjects.forEach(s => {
        const tr = document.createElement('tr');
        const gc = getGradeClass(s.grade);
        const sc = s.is_pass ? 'status-pass' : 'status-fail';
        const tc = s.is_practical ? 'type-practical' : 'type-theory';
        tr.innerHTML = `
            <td class="subject-name-cell">${s.name}</td>
            <td><span class="subject-type-badge ${tc}">${s.is_practical ? 'Practical' : 'Theory'}</span></td>
            <td>${s.ese ?? '—'}</td>
            <td>${s.ia ?? '—'}</td>
            <td style="font-weight:600;font-family:var(--font-mono)">${s.obtained}/${s.max}</td>
            <td><span class="grade-badge ${gc}">${s.grade || '—'}</span></td>
            <td style="text-align:center">${s.credit}</td>
            <td class="${sc}">${s.is_pass ? '✓ Pass' : '✗ Fail'}</td>`;
        tbody.appendChild(tr);
    });
    renderChart(subjects);
}

function renderChart(subjects) {
    const ctx = document.getElementById('subjects-chart').getContext('2d');
    if (subjectChart) subjectChart.destroy();

    const labels = subjects.map(s => s.name.length > 22 ? s.name.substring(0, 20) + '…' : s.name);
    const pcts = subjects.map(s => s.percentage);
    const colors = subjects.map(s => {
        if (!s.is_pass) return 'rgba(251,113,133,0.8)';
        if (s.percentage >= 75) return 'rgba(52,211,153,0.8)';
        if (s.percentage >= 60) return 'rgba(56,189,248,0.8)';
        if (s.percentage >= 45) return 'rgba(251,191,36,0.8)';
        return 'rgba(251,113,133,0.8)';
    });

    subjectChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{ label: 'Score %', data: pcts, backgroundColor: colors, borderColor: colors.map(c => c.replace('0.8', '1')), borderWidth: 1, borderRadius: 6, borderSkipped: false }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17,24,39,0.95)', titleColor: '#f1f5f9', bodyColor: '#94a3b8',
                    borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1, cornerRadius: 8, padding: 12,
                    callbacks: { label: (ctx) => { const s = subjects[ctx.dataIndex]; return `${s.obtained}/${s.max} (${s.percentage}%) — Grade: ${s.grade}`; } }
                }
            },
            scales: {
                y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { color: '#64748b', font: { size: 11 }, callback: v => v + '%' }, border: { display: false } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 }, maxRotation: 45 }, border: { display: false } }
            },
            animation: { duration: 800, easing: 'easeOutQuart' }
        }
    });
}

// ==========================================
// Helpers
// ==========================================

function titleCase(str) {
    return str.toLowerCase().split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function percentageColor(pct) {
    if (pct >= 75) return 'text-emerald';
    if (pct >= 60) return 'text-sky';
    if (pct >= 45) return 'text-amber';
    return 'text-rose';
}

function performanceColor(level) {
    if (!level) return '';
    const l = level.toLowerCase();
    if (l === 'excellent') return 'text-emerald';
    if (l === 'good') return 'text-sky';
    if (l === 'average') return 'text-amber';
    return 'text-rose';
}

function getGradeClass(grade) {
    if (!grade) return '';
    const g = grade.toUpperCase();
    if (g.startsWith('A') || g === 'O') return 'grade-a';
    if (g.startsWith('B')) return 'grade-b';
    if (g.startsWith('C')) return 'grade-c';
    if (g === 'P') return 'grade-p';
    if (g === 'F') return 'grade-f';
    return 'grade-p';
}

function shakeElement(el) {
    el.style.animation = 'none';
    el.offsetHeight;
    el.style.animation = 'shake 0.4s ease';
    setTimeout(() => el.style.animation = '', 400);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// Shake keyframe
const style = document.createElement('style');
style.textContent = `@keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-6px)} 50%{transform:translateX(6px)} 75%{transform:translateX(-4px)} }`;
document.head.appendChild(style);
