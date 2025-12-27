// =========================
// Element Checks (Avoid Errors)
// =========================
const videoForm = document.getElementById('video-form');
const stopButton = document.getElementById('stop-session');
const timerElement = document.getElementById('timer');
const videoContainer = document.getElementById('video-container');

let interval;

// =========================
// Start Focus Session
// =========================
if (videoForm) {
    videoForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const link = document.getElementById('youtube-link').value;
        const videoId = extractVideoId(link);
        const studyTimeInput = document.getElementById('study-time').value;
        const studyTime = parseInt(studyTimeInput);

        if (!studyTime || studyTime <= 0) {
            alert("Enter a valid study duration.");
            return;
        }

        if (videoId) {
            const embedUrl = `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0&showinfo=0`;
            videoContainer.innerHTML = `<iframe width="100%" height="315"
                src="${embedUrl}" allow="autoplay" allowfullscreen></iframe>`;

            startTimer(studyTime * 3600);
            stopButton.style.display = 'inline-block';
            enterFullscreen();
        } else {
            alert('Invalid YouTube link.');
        }
    });
}

// =========================
// Stop Session
// =========================
if (stopButton) {
    stopButton.addEventListener('click', stopSession);
}

function extractVideoId(url) {
    const regex = /(?:v=|\/)([a-zA-Z0-9_-]{11})(?:\?|&|$)/;
    const match = url.match(regex);
    return match ? match[1] : null;
}

function startTimer(seconds) {
    clearInterval(interval);
    
    interval = setInterval(() => {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;

        timerElement.textContent = `${h}h ${m}m ${s}s`;

        if (seconds-- <= 0) {
            clearInterval(interval);
            alert('Great job! Study session completed 🎉');
            stopSession();
        }
    }, 1000);
}

function stopSession() {
    clearInterval(interval);
    timerElement.textContent = 'Session stopped';
    videoContainer.innerHTML = '';
    stopButton.style.display = 'none';
    exitFullscreen();
}

// =========================
// Fullscreen Controls
// =========================
function enterFullscreen() {
    const elem = document.documentElement;
    if (elem.requestFullscreen) elem.requestFullscreen();
}

function exitFullscreen() {
    if (document.fullscreenElement && document.exitFullscreen) {
        document.exitFullscreen();
    }
}

// =========================
// Scroll Function For Landing Page
// =========================
function scrollToRegister() {
    const section = document.getElementById("register-form");
    if (section) section.scrollIntoView({ behavior: "smooth" });
}

// =========================
// Disable Right-Click & Developer Keys
// =========================
document.addEventListener('contextmenu', e => e.preventDefault());
document.addEventListener('keydown', e => {
    if (e.key === "F12" || (e.ctrlKey && ["N", "T", "W"].includes(e.key))) {
        e.preventDefault();
    }
});

// Warn on Exit During Session
window.addEventListener('beforeunload', function(e) {
    if (interval) {
        e.returnValue = "Your study session will be stopped.";
    }
});
