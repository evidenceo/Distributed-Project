// Slide
let calendar;
let averagePeriodLength;
let selectedPeriodId = null;
let periodsData = [];

document.addEventListener("DOMContentLoaded", function () {
    let currentSlide = 0;
    const slides = document.getElementsByClassName("slide");
    const showSlide = () => {
        Array.from(slides).forEach((slide, index) => {
            slide.style.display = index === currentSlide ? "block" : "none";
        });
    };

    showSlide();
    setInterval(() => {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide();
    }, 3000); // Slide change interval

    fetchUserCycleInfo();

});

// Calendar
function fetchUserCycleInfo() {
    fetch('/user-cycle-info')
        .then(response => response.json())
        .then(data => {
            if (data) {
                averagePeriodLength = data.average_period_length;
                periodsData = data.known_periods;
                initializeCalendar(data);
            }
        })
        .catch(error => console.error('Error fetching cycle info:', error));
}

function initializeCalendar(userData) {
    var events = [];

    // Add known periods to events
    userData.known_periods.forEach(period => {
        events.push({
            id: period.id,
            title: 'Known Period',
            start: period.start_date,
            end: period.end_date,
            color: 'red',
            textColor: 'white'
        });
    });

     // Add predicted periods to events
    userData.predictions.forEach(period => {
        events.push({
            title: 'Predicted Period',
            start: period.start_date,
            end: period.end_date,
            color: 'pink', // Color for predicted periods
            textColor: 'white'
        });
    });


    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        dateClick: function(info) {
           showPopup(info);
        },
        events: events
    });
    calendar.render();
}

function showPopup(info) {
    var popup = document.getElementById('dayPopup');

    // Calculate position based on the clicked date cell
    var calendarRect = document.getElementById('calendar').getBoundingClientRect();
    var xPosition = info.jsEvent.clientX - calendarRect.left;
    var yPosition = info.jsEvent.clientY - calendarRect.top;

    popup.style.left = xPosition + 'px';
    popup.style.top = yPosition + 'px';
    popup.style.display = 'block';

    // Check if clicked date is part of an existing period and get its ID
    selectedPeriodId = findPeriodIdByDate(info.dateStr);

    // Save the selected date
    selectedDate = info.dateStr;
}


function closePopup() {
    document.getElementById('dayPopup').style.display = 'none';

}

// Function to find a period's ID by a given date
function findPeriodIdByDate(dateStr) {
    // Iterate through the periods to find one that includes dateStr
    for (let period of periodsData) {
        if (dateStr >= period.start_date && dateStr <= period.end_date) {
            return period.id; // Return the ID of the period
        }
    }
    return null; // Return null if no period includes dateStr
}


function markPeriodStart(date) {
    var startDate = selectedDate; // Assuming selectedDate is in 'YYYY-MM-DD' format
    var endDate = calculateEndDate(startDate, averagePeriodLength); // You need to define this function based on your logic

    fetch('/add-period', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ start_date: startDate, end_date: endDate })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            refreshCalendarEvents();
        } else {
            // Handle error
            console.error('Failed to add period:', data.message);
        }
    })
    .catch(error => {
        console.error('Error adding period:', error);
    });
}

function markPeriodEnd(periodId) {
    var newEndDate = selectedDate; // Assuming selectedDate is the new end date

    fetch(`/update-period/${periodId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ end_date: newEndDate })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            refreshCalendarEvents();
        } else {
            // Handle error
            console.error('Failed to update period:', data.message);
        }
    })
    .catch(error => {
        console.error('Error updating period:', error);
    });
}

function deletePeriod() {
    if (selectedPeriodId !== null) {
        fetch(`/delete-period/${selectedPeriodId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                refreshCalendarEvents();
            } else {
                // Handle error
                console.error('Failed to delete period:', data.message);
            }
        })
        .catch(error => {
            console.error('Error deleting period:', error);
        });
    } else {
        console.error('No period selected or period ID not found');
    }
}



function refreshCalendarEvents() {
    fetchUserCycleInfo(); // This should re-fetch user cycle data and re-initialize the calendar
}




// Helper functions
function calculateEndDate(startDate, averagePeriodLength) {
    // Convert the start date string to a Date object
    let startDateObj = new Date(startDate);

    // Add the average period length to the start date
    startDateObj.setDate(startDateObj.getDate() + averagePeriodLength);

    // Convert the date object back to a string in 'YYYY-MM-DD' format
    let endDate = startDateObj.toISOString().split('T')[0];

    return endDate;
}




