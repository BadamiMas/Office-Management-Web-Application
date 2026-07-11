/* ============================================
   MAIN.JS — replaces acc.js, head.js, hr.js,
   accjob.js, headjob.js, hrjob.js, doc.js,
   job.js, test.js (shared logic only)
   ============================================ */


// ============
// SIDEBAR + THEME TOGGLE
// ============
const sidemenu = document.querySelector("aside");
const menubtn = document.querySelector("#menu-bar");
const closebtn = document.querySelector("#close-btn");
const themeToggler = document.querySelector(".theme-toggler");

menubtn.addEventListener("click", () => sidemenu.style.display = "block");
closebtn.addEventListener("click", () => sidemenu.style.display = "none");

// Apply saved theme on every page load
if (localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-theme-variables");
    themeToggler.querySelector("span:nth-child(1)").classList.remove("active");
    themeToggler.querySelector("span:nth-child(2)").classList.add("active");
}

themeToggler.addEventListener("click", () => {
    document.body.classList.toggle("dark-theme-variables");
    const isDark = document.body.classList.contains("dark-theme-variables");
    
    // save to localStorage
    localStorage.setItem("theme", isDark ? "dark" : "light");

    themeToggler.querySelector("span:nth-child(1)").classList.toggle("active");
    themeToggler.querySelector("span:nth-child(2)").classList.toggle("active");
});


/* ============
   TO-DO LIST
   ============ */
const inputBox = document.getElementById('input-box');
const listContainer = document.getElementById('list');

function addTask() {
    if (!inputBox.value.trim()) { alert("You must write something!"); return; }
    let li = document.createElement("li");
    li.innerHTML = inputBox.value;
    let span = document.createElement("span");
    span.innerHTML = "\u00d7";
    li.appendChild(span);
    listContainer.appendChild(li);
    inputBox.value = "";
    saveData();
}

listContainer.addEventListener("click", function(e) {
    if (e.target.tagName === "LI") { e.target.classList.toggle("checked"); saveData(); }
    else if (e.target.tagName === "SPAN") { e.target.parentElement.remove(); saveData(); }
});

function saveData() {
    localStorage.setItem("data", listContainer.innerHTML);
    updatePendingCount();
}

function updatePendingCount() {
    const el = document.getElementById("pending-count");
    if (!el) return; // not every page has this element
    el.innerText = listContainer.querySelectorAll("li:not(.checked)").length;
}

function showTask() { listContainer.innerHTML = localStorage.getItem("data") || ""; }
showTask();
updatePendingCount();


/* ============
   DATE (replaces the inline <script> in every HTML file)
   ============ */
const dateInput = document.getElementById('today-date');
if (dateInput) {
    const today = new Date();
    const dd = String(today.getDate()).padStart(2, '0');
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const yyyy = today.getFullYear();
    dateInput.value = `${yyyy}-${mm}-${dd}`;
}


/* ============
   ATTENDANCE LOG
   ============ */
function parseTime(timeStr) {
    const [time, period] = timeStr.split(' ');
    let [hours, minutes] = time.split(':').map(Number);
    if (period === 'PM' && hours !== 12) hours += 12;
    if (period === 'AM' && hours === 12) hours = 0;
    const d = new Date();
    d.setHours(hours, minutes, 0, 0);
    return d;
}

function displayAttendance() {
    fetch('/get_attendance')
        .then(r => r.json())
        .then(data => {
            const loginEl = document.getElementById("login-time");
            const logoutEl = document.getElementById("logout-time");
            const activeEl = document.getElementById("active-hours");  // ← was missing!
            if (!loginEl) return;

            loginEl.innerText = data.login_time || "-";
            logoutEl.innerText = data.logout_time || "-";

            if (data.login_time && activeEl) {
                const loginTime = parseTime(data.login_time);
                const endTime = data.logout_time ? parseTime(data.logout_time) : new Date();
                const diffHours = ((endTime - loginTime) / (1000 * 60 * 60)).toFixed(2);
                activeEl.innerText = diffHours;
            }
        })
        .catch(err => console.error('Attendance error:', err));
}

displayAttendance();
setInterval(displayAttendance, 60000);


/* ============
   TOTAL EMPLOYEES
   ============ */
function loadTotalEmployees() {
    const el = document.getElementById('total-employees');
    if (!el) return; // not every page needs this
    fetch('/get_total_employees')
        .then(r => r.json())
        .then(data => el.innerText = data.total_employees)
        .catch(err => console.error('Error loading employees:', err));
}

loadTotalEmployees();
setInterval(loadTotalEmployees, 600000);

/* ============
   TABLE PAGINATION
   ============ */
let allRows = [];
let currentPage = 1;
const rowsPerPage = 10;

function initPagination(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const tbody = table.querySelector('tbody');
    allRows = Array.from(tbody.querySelectorAll('tr'));

    renderPage(1);
}

function renderPage(page) {
    const searchInput = document.getElementById('employeeSearch');
    const query = searchInput ? searchInput.value.toLowerCase() : '';

    // filter by search first
    const filtered = allRows.filter(row => 
        row.innerText.toLowerCase().includes(query)
    );

    const totalPages = Math.ceil(filtered.length / rowsPerPage) || 1;
    currentPage = Math.min(page, totalPages);

    // hide all rows first
    allRows.forEach(row => row.style.display = 'none');

    // show only current page rows
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    filtered.slice(start, end).forEach(row => row.style.display = '');

    // render pagination buttons
    const container = document.querySelector('.pagination');
    if (!container) return;
    container.innerHTML = '';

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.innerText = i;
        btn.className = 'page-btn' + (i === currentPage ? ' active' : '');
        btn.onclick = () => renderPage(i);
        container.appendChild(btn);
    }
}

// override searchTable to work with pagination
function searchTable() {
    renderPage(1);
}

if (document.getElementById('employeeTable')) {
    // create pagination container
    const table = document.getElementById('employeeTable');
    const div = document.createElement('div');
    div.className = 'pagination';
    table.parentElement.appendChild(div);

    initPagination('employeeTable');
}

/* ============
   PROFILE POPUP (for pages that have it)
   ============ */
const openProfile = document.getElementById("openProfile");
const profilePop = document.getElementById("profilePop");
const closeProfile = document.getElementById("closeProfile");

if (openProfile && profilePop && closeProfile) {
    openProfile.addEventListener("click", () => profilePop.classList.add("open"));
    closeProfile.addEventListener("click", () => profilePop.classList.remove("open"));
}

function searchSetup() {
    const input = document.getElementById('setupSearch').value.toLowerCase();
    const rows = document.querySelectorAll('#setupTable tbody tr');
    rows.forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(input) ? '' : 'none';
    });
}


/* ============
   QUOTATIONS & INVOICES
   ============ */

function addInvLineItem() {
    const tbody = document.getElementById('invLineItemsBody');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" name="li_desc[]" placeholder="Description" style="width:100%; background:#630000; color:#d1ffd1; border:none; padding:4px; border-radius:3px;"></td>
        <td><input type="number" step="0.01" name="li_qty[]" placeholder="0" oninput="updateAmount(this)" style="width:100%; background:#630000; color:#d1ffd1; border:none; padding:4px; border-radius:3px;"></td>
        <td><input type="number" step="0.01" name="li_rate[]" placeholder="0.00" oninput="updateAmount(this)" style="width:100%; background:#630000; color:#d1ffd1; border:none; padding:4px; border-radius:3px;"></td>
        <td class="amt-cell" style="padding:4px; font-size:0.82rem; text-align:right;">$0.00</td>
        <td><button type="button" onclick="this.closest('tr').remove(); updateTotals()" style="background:#8B0000; color:#fff; border:none; border-radius:3px; padding:3px 8px; cursor:pointer;">✕</button></td>
    `;
    tbody.appendChild(tr);
}

function updateAmount(input) {
    const row   = input.closest('tr');
    const qty   = parseFloat(row.querySelector('[name="li_qty[]"]').value) || 0;
    const rate  = parseFloat(row.querySelector('[name="li_rate[]"]').value) || 0;
    row.querySelector('.amt-cell').textContent = '$' + (qty * rate).toFixed(2);
    updateTotals();
}

function updateTotals() {
    let sub = 0;
    document.querySelectorAll('.amt-cell').forEach(td => {
        sub += parseFloat(td.textContent.replace('$','')) || 0;
    });
    const gst   = sub * 0.09;
    const total = sub + gst;
    document.getElementById('subtotalDisp').textContent = '$' + sub.toFixed(2);
    document.getElementById('gstDisp').textContent      = '$' + gst.toFixed(2);
    document.getElementById('totalDisp').textContent    = '$' + total.toFixed(2);
}

function searchInvoices() {
    const q = document.getElementById('invSearch').value.toLowerCase();
    document.querySelectorAll('#invTable tbody tr').forEach(r => {
        r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

// init totals on load
if (document.getElementById('subtotalDisp')) updateTotals();

function toggleQuoteType() {
    const t = document.getElementById('quoteType').value;
    document.getElementById('manpowerSection').style.display  = t === 'manpower'  ? '' : 'none';
    document.getElementById('lineitemsSection').style.display = t === 'lineitems' ? '' : 'none';
}

function addLineItem() {
    const tbody = document.getElementById('lineItemsBody');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" name="li_desc[]" placeholder="Description" style="width:100%; background:#630000; color:#d1ffd1; border:none; padding:4px; border-radius:3px;"></td>
        <td><input type="number" step="0.01" name="li_qty[]" placeholder="0" style="width:100%; background:#630000; color:#d1ffd1; border:none; padding:4px; border-radius:3px;"></td>
        <td><input type="number" step="0.01" name="li_rate[]" placeholder="0.00" style="width:100%; background:#630000; color:#d1ffd1; border:none; padding:4px; border-radius:3px;"></td>
        <td><button type="button" onclick="this.closest('tr').remove()" style="background:#8B0000; color:#fff; border:none; border-radius:3px; padding:3px 8px; cursor:pointer;">✕</button></td>
    `;
    tbody.appendChild(tr);
}

function searchQuotes() {
    const q = document.getElementById('quoteSearch').value.toLowerCase();
    document.querySelectorAll('#quoteTable tbody tr').forEach(r => {
        r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

// init on load
if (document.getElementById('quoteType')) toggleQuoteType();



/* ============
   AUTO LOGOUT (inactivity timer — 10 mins)
   ============ */
let logoutTimer;
function resetTimer() {
    clearTimeout(logoutTimer);
    logoutTimer = setTimeout(() => window.location.href = "/logout", 600000);
}

window.addEventListener("load", resetTimer);
window.addEventListener("mousemove", resetTimer);
window.addEventListener("keypress", resetTimer);
