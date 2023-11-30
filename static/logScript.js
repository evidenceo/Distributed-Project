let recordExists = false; // Flag to track if record exists

document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const dateString = urlParams.get('date') || new Date().toISOString().split('T')[0]; // Default to today if no date is provided
    const dateParts = dateString.split('-');

    // Create a new Date object from parts to avoid timezone issues
    const date = new Date(dateParts[0], dateParts[1] - 1, dateParts[2]);

    document.getElementById('current-date').textContent = formatDate(new Date(date));

    // Event listeners for navigating dates
    document.getElementById('prev-day').addEventListener('click', () => changeDate(-1));
    document.getElementById('next-day').addEventListener('click', () => changeDate(1));
});

function formatDate(date) {
    // Format the date as you prefer to display
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

function changeDate(change) {
    const currentDate = new Date(document.getElementById('current-date').textContent);
    currentDate.setDate(currentDate.getDate() + change);
    document.getElementById('current-date').textContent = formatDate(currentDate);
    clearForm();
    clearUIData();
    fetchSymptomsForDate(currentDate);
}

function fetchSymptomsForDate(date) {
    const formattedDate = formatDateForAPI(date);

    fetch(`/get-symptoms?date=${formattedDate}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Received data:', data);
            // Assuming 'data' contains the symptoms information for the given date
            updateUI(data);
        })
        .catch(error => {
            console.error('Error fetching symptoms:', error);
        });
}


function formatDateForAPI(date) {
    // Assuming 'date' is a JavaScript Date object
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
}


function clearForm() {
    document.getElementById('symptoms-form').reset();
    // Additionally, clear any dynamically added content if needed
    // For example, clear lists, uncheck checkboxes, etc.
}

function clearUIData() {
    // Clear the data shown in the UI
    document.getElementById('flow-list').innerHTML = '';
    document.getElementById('med-list').innerHTML = '';
    document.getElementById('sex-list').innerHTML = '';
    document.getElementById('symptoms-list').innerHTML = '';
    document.getElementById('mood-list').innerHTML = '';
    document.getElementById('notes-list').innerHTML = '';
}

document.addEventListener('DOMContentLoaded', function() {
    // Event listeners for modal buttons
    setupModalToggle('flow-btn', 'flow-modal');
    setupModalToggle('med-btn', 'med-modal');
    setupModalToggle('sex-btn', 'sex-modal');
    setupModalToggle('symptom-btn', 'sym-modal');
    setupModalToggle('mood-btn', 'mood-modal');

    // Handle form submissions
    const saveButton = document.getElementById('add-symptoms');
    saveButton.addEventListener('click', handleSave);
});

function setupModalToggle(buttonId, modalId) {
    const button = document.getElementById(buttonId);
    const modal = document.getElementById(modalId);
    const closeModal = modal.querySelector('.close-modal');

    button.addEventListener('click', function() {
        modal.style.display = 'block';
    });

    closeModal.addEventListener('click', function() {
        modal.style.display = 'none';
    });
}

function handleSave(event) {
    event.preventDefault();
    const formData = new FormData();

    // Collect data from flow checkboxes
    const flowCheckboxes = document.querySelectorAll('#flow-modal input[type="checkbox"]:checked');
    formData.append('flow', Array.from(flowCheckboxes).map(cb => cb.value).join(', '));

    // Collect data from other medicine
    const medicineInput = document.getElementById('medicine');
    if (medicineInput) {
        formData.append('medicine', medicineInput.value);
    }

    // Collect data from intercourse checkboxes
    const intercourseCheckboxes = document.querySelectorAll('#sex-modal input[type="checkbox"]:checked');
    formData.append('sex', Array.from(intercourseCheckboxes).map(cb => cb.value).join(', '));

    // Collect data from symptoms checkboxes
    const symptomCheckboxes = document.querySelectorAll('#sym-modal input[type="checkbox"]:checked');
    formData.append('symptom', Array.from(symptomCheckboxes).map(cb => cb.value).join(', '));

    // Collect data from mood checkboxes
    const moodCheckboxes = document.querySelectorAll('#mood-modal input[type="checkbox"]:checked');
    formData.append('mood', Array.from(moodCheckboxes).map(cb => cb.value).join(', '));

    // Collect data from Additional notes
    const additionalNotes = document.getElementById('add-notes');
    if (additionalNotes) {
        formData.append('add-notes', additionalNotes.value);
    }

    // Get the date from the UI and format it correctly
    const currentDateElement = document.getElementById('current-date');
    if (currentDateElement) {
        const dateString = currentDateElement.textContent;
        const formattedDate = formatDateForSubmission(dateString);
        if (formattedDate) {
            formData.append('date', formattedDate);
        } else {
            console.error('Invalid date format:', dateString);
            return; // Exit the function if the date format is invalid
        }
    } else {
        console.error('Date element not found');
        return; // Exit the function if the date element is not found
    }

    // Convert FormData to a JSON object
    const objectData = Object.fromEntries(formData.entries());
    const jsonData = JSON.stringify(objectData);

    // Send to server
    fetch('/save-symptoms', {
        method: 'POST',
        body: jsonData,
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        // Update UI here based on response
        updateUI(objectData);
    })
    .catch(error => console.error('Error:', error));
}


// Function to format the date from "Month Day, Year" to "YYYY-MM-DD"
function formatDateForSubmission(dateString) {
    const dateObj = new Date(dateString);
    if (!isNaN(dateObj.getTime())) {
        // Format date as YYYY-MM-DD
        return dateObj.toISOString().split('T')[0];
    } else {
        return null; // Return null if the date is invalid
    }
}

function updateUI(formData) {
    // Display a success message
    const messageBox = document.getElementById('message-box');
    if (messageBox) {
        messageBox.textContent = "Symptoms saved successfully!";
        messageBox.style.display = "block";
    }

    // Update flow data
    const flowData = document.getElementById('flow-list');
    updateOrCreateListItem(flowData, 'Flow', formData.flow);

    const medicineData = document.getElementById('med-list');
    updateOrCreateListItem(medicineData, 'Medicine', formData.medicine);

    const intercourseData = document.getElementById('sex-list');
    updateOrCreateListItem(intercourseData, 'Intercourse', formData.sex);

    const symptomsList = document.getElementById('symptoms-list');
    updateOrCreateListItem(symptomsList, 'Symptoms', formData.symptom);

    const moodList = document.getElementById('mood-list');
    updateOrCreateListItem(moodList, 'Mood', formData.mood);

    const notesList = document.getElementById('notes-list');
    updateOrCreateListItem(notesList, 'Additional Notes', formData.notes);

    // Close any open modals if necessary
    closeAllModals();
}

function updateOrCreateListItem(parentElement, label, data) {
    if (!parentElement || !data) return;
    let item = parentElement.querySelector(`li[data-category="${label}"]`);
    if (!item) {
        item = document.createElement('li');
        item.setAttribute('data-category', label);
        parentElement.appendChild(item);
    }
    item.textContent = `${label}: ${data}`;
}

// Helper function to close all modals
function closeAllModals() {
    const modals = document.querySelectorAll('.sym-modal');
    modals.forEach(modal => modal.style.display = 'none');
}












