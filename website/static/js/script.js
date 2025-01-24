document.addEventListener('DOMContentLoaded', function(){
    //date picker algorithm
    const dateInput = document.querySelector('#dateSelect');

    const today = new Date();

    const maxDate = new Date(today);
    maxDate.setDate(today.getDate() + 30);

    if (maxDate.getDate() === 31) {
        maxDate.setDate(31);
    }

    dateInput.setAttribute('min', today.toISOString().split('T')[0]);
    dateInput.setAttribute('max', maxDate.toISOString().split('T')[0]);

    
});


function setAvailabeHours(){
    const selectedDate = document.getElementById("dateSelect").value;
    fetch(`/appointments/${selectedDate}`)
        .then(response => response.json())
        .then(data => {
            let hoursDiv = document.getElementById("hours");
            hoursDiv.innerHTML = "";

            if (data.available_hours.length === 0) {
                hoursDiv.innerHTML = "<p>No slots available.</p>";
                return;
            }

            data.available_hours.forEach(hour => {
                let button = document.createElement("button");
                button.innerText = hour;
                button.onclick = () => alert(`You selected ${hour}`);
                hoursDiv.appendChild(button);
            });
        });
}