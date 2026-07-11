/* ============================================
   CHARTS.JS — replaces chart logic scattered
   across acc.js, head.js, hr.js, test.js
   ============================================ */

google.charts.load('current', { packages: ['corechart'] });

function initChart(role) {
    google.charts.setOnLoadCallback(() => drawChart(role));
    window.addEventListener('resize', () => drawChart(role));
    setInterval(() => drawChart(role), 60000);
}

function drawChart(role) {
    if (role === 'Head') {
        drawHeadChart();
    } else if (role === 'HR') {
        drawHRChart();
    } else if (role === 'Accountant') {
        drawAccChart();
    } else {
        // default fallback (test.html / unknown role)
        drawAccChart();
    }
}


/* ============
   HEAD — combo chart (cash in/out + employees)
   ============ */
function drawHeadChart() {
    fetch('/get_company_progress')
        .then(r => r.json())
        .then(rows => {
            const dataArray = [['Month', 'Cash In (SGD)', 'Cash Out (SGD)', 'Employees']];
            rows.forEach(row => {
                const monthName = new Date(2025, row.month - 1).toLocaleString('default', { month: 'short' });
                dataArray.push([monthName, parseFloat(row.cash_in), parseFloat(row.cash_out), parseInt(row.employees)]);
            });

            const data = google.visualization.arrayToDataTable(dataArray);
            const options = {
                vAxes: {
                    0: { title: 'Cash Flow (SGD)', textStyle: { color: '#fff' }, titleTextStyle: { color: '#fff' } },
                    1: { title: 'Employees', textStyle: { color: '#fff' }, titleTextStyle: { color: '#fff' } }
                },
                hAxis: { textStyle: { color: '#fff' }, titleTextStyle: { color: '#fff' } },
                seriesType: 'bars',
                series: {
                    0: { type: 'bars', targetAxisIndex: 0, color: '#3cb424' },
                    1: { type: 'bars', targetAxisIndex: 0, color: '#e53935' },
                    2: { type: 'line', targetAxisIndex: 1, color: '#e6e798' }
                },
                backgroundColor: 'transparent',
                chartArea: { width: '80%', height: '70%' },
                legend: { position: 'bottom', textStyle: { color: '#fff' } }
            };

            new google.visualization.ComboChart(document.getElementById('chart_div')).draw(data, options);
        })
        .catch(err => console.error('Head chart error:', err));
}


/* ============
   HR — line chart (employees hired)
   ============ */
function drawHRChart() {
    fetch('/get_company_progress_hr')
        .then(r => r.json())
        .then(rows => {
            const dataArray = [['Month', 'Employees']];
            rows.forEach(row => {
                const monthName = new Date(row.year, row.month - 1).toLocaleString('default', { month: 'short' });
                dataArray.push([monthName, parseInt(row.employees)]);
            });

            const data = google.visualization.arrayToDataTable(dataArray);
            const options = {
                title: 'Employees Recruited (Last 6 Months)',
                titleTextStyle: { color: '#fff', fontSize: 16, bold: true },
                curveType: 'function',
                legend: { position: 'bottom', textStyle: { color: '#fff' } },
                hAxis: { textStyle: { color: '#fff' } },
                vAxis: { textStyle: { color: '#fff' } },
                backgroundColor: 'transparent',
                chartArea: { width: '80%', height: '70%' },
                series: { 0: { color: '#21c700' } }
            };

            new google.visualization.LineChart(document.getElementById('chart_div')).draw(data, options);
        })
        .catch(err => console.error('HR chart error:', err));
}


/* ============
   ACCOUNTANT — column chart (cash in/out)
   ============ */
function drawAccChart() {
    fetch('/get_company_progress_acc')
        .then(r => r.json())
        .then(rows => {
            const data = google.visualization.arrayToDataTable([
                ['Month', 'Cash In', 'Cash Out'],
                ...rows.map(r => [r.month, r.cash_in, r.cash_out])
            ]);

            const options = {
                title: 'Cash In & Out (Last 6 Months)',
                titleTextStyle: { color: '#fff', fontSize: 16 },
                chartArea: { width: '80%', height: '70%' },
                backgroundColor: 'transparent',
                legend: { position: 'bottom', textStyle: { color: '#fff' } },
                hAxis: { textStyle: { color: '#fff' } },
                vAxis: { textStyle: { color: '#fff' } },
                series: {
                    0: { color: '#3cb424' },
                    1: { color: '#e53935' }
                },
                bar: { groupWidth: '60%' }
            };

            new google.visualization.ColumnChart(document.getElementById('chart_div')).draw(data, options);
        })
        .catch(err => console.error('Acc chart error:', err));
}
