/**
 * QR Attendance Tracking System
 * Main JavaScript file
 */
document.addEventListener('DOMContentLoaded', function () {
    initializeTooltips();
    animateCards();
    setupAlerts();
    setupFormValidation();
    setupQRDownload();
    
    // Attach event listener to check-in button
    const checkInButton = document.getElementById('check-in-btn');
    if (checkInButton) {
        checkInButton.addEventListener('click', openScannerScreen);
    }
});

/**
 * Function to show scanner screen with start scanning button
 */
function openScannerScreen() {
    const scannerContainer = document.getElementById('qr-scanner-container');
    
    // Add the scanner UI dynamically
    scannerContainer.innerHTML = `
        <div class="scanner-popup">
            <h3>Scan QR Code</h3>
            <div id="qr-scanner"></div>
            <button id="start-scan-btn" class="btn btn-primary mt-3">Start Scanning</button>
            <button id="close-scan-btn" class="btn btn-danger mt-2">Close</button>
        </div>
    `;
    
    scannerContainer.style.display = 'block'; // Show scanner container
    
    // Attach event listeners for buttons
    document.getElementById('start-scan-btn').addEventListener('click', initializeQRScanner);
    document.getElementById('close-scan-btn').addEventListener('click', function () {
        scannerContainer.style.display = 'none';
    });
}

/**
 * Initialize QR code scanner functionality
 */
function initializeQRScanner() {
    console.log("Initializing QR Scanner...");

    // Request camera permission
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(() => {
            console.log("✅ Camera access granted");

            const scannerElement = document.getElementById('qr-scanner');
            scannerElement.innerHTML = ""; // Clear previous scanner UI
            
            let html5QrcodeScanner = new Html5QrcodeScanner("qr-scanner", {
                fps: 10,
                qrbox: 250
            });

            html5QrcodeScanner.render((decodedText) => {
                console.log("✅ QR Code Scanned:", decodedText);

                // Send check-in request
                fetch('/api/attendance/check-in/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ qr_data: decodedText })
                })
                .then(response => response.json())
                .then(data => {
                    console.log('✅ Check-in success:', data);
                    window.location.href = '/dashboard/';
                })
                .catch(error => {
                    console.error('❌ Error checking in:', error);
                });
            });
        })
        .catch(err => {
            console.error("❌ Camera access denied:", err);
            alert("Camera permission denied. Please allow camera access to scan QR codes.");
        });
}
