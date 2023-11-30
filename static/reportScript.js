document.addEventListener("DOMContentLoaded", function() {
    fetchReportData();
});

function fetchReportData() {
    fetch('/report-data')
    .then(response => response.json())
    .then(data => {
        displayReportData(data);
    })
    .catch(error => console.error('Error:', error));
}

function displayReportData(data) {
    const avgPeriodLengthElement = document.getElementById('avg-period-length');
    const avgCycleLengthElement = document.getElementById('avg-cycle-length');
    const fertilityWindowElement = document.getElementById('current-fertility-window');

    if (avgPeriodLengthElement) {
        avgPeriodLengthElement.textContent = data.average_period_length + ' days';
    }
    if (avgCycleLengthElement) {
        avgCycleLengthElement.textContent = data.average_cycle_length + ' days';
    }
    if (fertilityWindowElement) {
        fertilityWindowElement.textContent = `${data.fertility_window.start} to ${data.fertility_window.end}`;
    }
}

function fetchAndDisplayCycleData() {
    // Fetch past cycles
    fetch('/past-cycles')
    .then(response => response.json())
    .then(data => {
        populateCycleTable(data, 'past-cycle-table');
    })
    .catch(error => console.error('Error:', error));

    // Fetch predicted cycles
    fetch('/predicted-cycles')
    .then(response => response.json())
    .then(data => {
        populateCycleTable(data, 'predicted-cycle-table');
    })
    .catch(error => console.error('Error:', error));
}

function populateCycleTable(cycles, tableId) {
    const table = document.getElementById(tableId);
    cycles.forEach(cycle => {
        const row = table.insertRow();
        const cell = row.insertCell();
        cell.textContent = `${cycle.start_date} - ${cycle.end_date}`;
    });
}

// Call this function when the page loads
fetchAndDisplayCycleData();


