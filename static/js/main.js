/* ─── NEXUS MEDIA — INTEGRATED AUDIO & DATA SYSTEM — FIXED PLAYBACK ─── */

// ─── NAVBAR ENVIRONMENT STYLES ───
window.addEventListener('scroll', () => {
    const nav = document.getElementById('mainNav');
    if (nav) nav.classList.toggle('scrolled', window.scrollY > 50);
});

function toggleMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileMenu) mobileMenu.classList.toggle('open');
}

// ─── SYSTEM NOTIFICATION TOAST CORE ────────
function showToast(msg, type = 'info', duration = 3500) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    // FIX: Clear out any pre-existing stuck warning cards before building a new one
    container.innerHTML = '';

    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = msg;
    container.appendChild(t);

    setTimeout(() => {
        t.style.opacity = '0';
        t.style.transform = 'translateX(120%)';
        t.style.transition = 'all .3s ease';
        setTimeout(() => t.remove(), 300);
    }, duration);
}


/* ──────────────────────────────────────────────────────────────────
    🎵 CORE HTML5 AUDIO STREAM ENGINE
   ────────────────────────────────────────────────────────────────── */
let currentTrackId = null;
let isPlaying = false;
let playlist = [];
let currentIndex = 0;

const audio = document.getElementById('audioPlayer');
const playerBar = document.getElementById('playerBar');
const playPauseBtn = document.getElementById('playPauseBtn');
const progressFill = document.getElementById('progressFill');
const progressThumb = document.getElementById('progressThumb');
const currentTimeEl = document.getElementById('currentTime');
const totalTimeEl = document.getElementById('totalTime');

function formatTime(seconds) {
    if (isNaN(seconds)) return "0:00";
    const m = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${sec}`;
}

/**
 * Custom Promise Wrapper that shields the stream architecture from modern 
 * browser autoplay blockades and handles sequential notifications safely.
 */
function playMediaStream(audioElement, trackTitle = "") {
    if (!audioElement) return;

    audioElement.muted = false;
    const playPromise = audioElement.play();

    if (playPromise !== undefined) {
        playPromise
            .then(() => {
                console.log("Media stream stabilization successful. Playback active.");
                isPlaying = true;
                if (playPauseBtn) playPauseBtn.textContent = '⏸';

                // Show success toast ONLY after the browser actively confirms playback is working
                if (trackTitle) {
                    showToast(`♪ Streaming: ${trackTitle}`, 'success');
                }
            })
            .catch(error => {
                console.warn("Autoplay block sequence engaged:", error);

                // Display exactly one single message guiding the user interaction fallback
                showToast("Playback blocked. Please click anywhere on the screen to listen.", "info");

                // Fallback Interaction Vector: Bind a single-use screen click target
                const forcePlayOnInteraction = () => {
                    audioElement.play()
                        .then(() => {
                            isPlaying = true;
                            if (playPauseBtn) playPauseBtn.textContent = '⏸';
                            if (trackTitle) {
                                showToast(`♪ Streaming: ${trackTitle}`, 'success');
                            }
                            document.removeEventListener('click', forcePlayOnInteraction);
                        })
                        .catch(err => console.error("Secondary playback attempt aborted:", err));
                };

                document.addEventListener('click', forcePlayOnInteraction);
            });
    }
}

/* ─── NEXUS MEDIA — INTEGRATED AUDIO & DATA SYSTEM ─── */

// ... (Keep all your existing code above playTrack exactly as it is) ...

/**
 * Loads a real file track URL into the native browser hardware stream layer.
 */
function playTrack(id, title, artist, thumb, fileUrl) {
    if (!audio) {
        showToast("Audio player engine element not found in DOM configuration.", "error");
        return;
    }

    currentTrackId = id;

    // Update player track details
    const titleEl = document.getElementById('playerTitle');
    const artistEl = document.getElementById('playerArtist');
    const thumbEl = document.getElementById('playerThumb');

    if (titleEl) titleEl.textContent = title;
    if (artistEl) artistEl.textContent = artist;
    if (thumb && thumbEl) {
        thumbEl.innerHTML = `<img src="${thumb}" alt="${title}" style="width:100%;height:100%;object-fit:cover;border-radius:4px;">`;
    }

    // Assign the file URL path
    if (fileUrl && fileUrl !== 'None' && fileUrl !== '') {
        audio.src = fileUrl;
    } else {
        audio.src = 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3';
        showToast("Playing preview stream (No raw track file uploaded yet)", "info");
    }

    if (playerBar) playerBar.classList.add('visible');

    // NEW: Save state to localStorage so it persists through page loads
    localStorage.setItem('nexus_player_state', JSON.stringify({
        id, title, artist, thumb, fileUrl
    }));

    // Route play event
    playMediaStream(audio, title);

    // Fire log metrics
    fetch(`/api/play/${id}`, { method: 'POST' }).catch(() => { });
}

// ... (Keep all your existing code: togglePlay, closePlayer, etc.) ...

/* ─── NEW: PERSISTENCE LAYER (Add this to the bottom of your file) ──── */

window.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('nexus_player_state');
    if (saved) {
        const data = JSON.parse(saved);
        const audio = document.getElementById('audioPlayer');
        const playerBar = document.getElementById('playerBar');

        // 1. Restore UI
        document.getElementById('playerTitle').textContent = data.title;
        document.getElementById('playerArtist').textContent = data.artist;
        document.getElementById('playerThumb').innerHTML = `<img src="${data.thumb}" style="width:100%;height:100%;object-fit:cover;border-radius:4px;">`;

        // 2. Restore Audio Source
        audio.src = data.fileUrl;

        // 3. Show the player bar
        if (playerBar) playerBar.classList.add('visible');

        console.log("Audio state restored from storage.");
    }
});

// ─── HERO VINYL MOUSE PARALLAX MOTION EFFECTS ────
document.addEventListener('mousemove', (e) => {
    const vinyl = document.querySelector('.vinyl-disc');
    if (!vinyl) return;
    const mx = (e.clientX / window.innerWidth - 0.5) * 10;
    const my = (e.clientY / window.innerHeight - 0.5) * 10;
    vinyl.style.transform = `rotate(${Date.now() / 100 % 360}deg) translate(${mx}px, ${my}px)`;
});

// ... (Keep your existing admin functions here) ...

function togglePlay() {
    if (!audio || (!audio.src && !currentTrackId)) return;

    if (isPlaying) {
        audio.pause();
        if (playPauseBtn) playPauseBtn.textContent = '▶';
        isPlaying = false;
    } else {
        const titleEl = document.getElementById('playerTitle');
        const currentTitle = titleEl ? titleEl.textContent : "";
        playMediaStream(audio, currentTitle);
    }
}

function closePlayer() {
    if (!audio) return;
    audio.pause();
    audio.src = '';
    if (playerBar) playerBar.classList.remove('visible');
    isPlaying = false;
    currentTrackId = null;
}

function setVolume(val) {
    if (audio) audio.volume = val / 100;
}

function seek(e) {
    if (!audio || !audio.duration) return;
    const bar = e.currentTarget;
    const rect = bar.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    audio.currentTime = pct * audio.duration;
}

function prevTrack() { showToast('Previous track sequence', 'info'); }
function nextTrack() { showToast('Next track sequence', 'info'); }

// Wire up Native Runtime Audio Object State Event Listeners
if (audio) {
    audio.addEventListener('timeupdate', () => {
        if (!audio.duration) return;
        const pct = (audio.currentTime / audio.duration) * 100;
        if (progressFill) progressFill.style.width = pct + '%';
        if (progressThumb) progressThumb.style.left = pct + '%';
        if (currentTimeEl) currentTimeEl.textContent = formatTime(audio.currentTime);
    });

    audio.addEventListener('loadedmetadata', () => {
        if (totalTimeEl) totalTimeEl.textContent = formatTime(audio.duration);
    });

    audio.addEventListener('ended', () => {
        if (playPauseBtn) playPauseBtn.textContent = '▶';
        isPlaying = false;
        if (progressFill) progressFill.style.width = '0%';
    });
}

// ─── CARD ENTRANCE INTERSECTION OBSERVATION ANIMATIONS ────
const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
            entry.target.style.animationDelay = `${(i % 6) * 0.08}s`;
            entry.target.classList.add('anim-in');
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.1 });

document.querySelectorAll('.card, .browse-card, .movie-card, .track-row, .dl-item').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity .5s ease, transform .5s ease';
    observer.observe(el);
});

document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = '.anim-in { opacity: 1 !important; transform: none !important; }';
    document.head.appendChild(style);
});

// ─── VOLUME CONTROL ATTACHMENT SLIDER INIT ────
const volSlider = document.getElementById('volumeSlider');
if (volSlider && audio) {
    audio.volume = 0.75;
    volSlider.addEventListener('input', function () {
        audio.volume = this.value / 100;
    });
}

// ─── HERO VINYL MOUSE PARALLAX MOTION EFFECTS ────
document.addEventListener('mousemove', (e) => {
    const vinyl = document.querySelector('.vinyl-disc');
    if (!vinyl) return;
    const mx = (e.clientX / window.innerWidth - 0.5) * 10;
    const my = (e.clientY / window.innerHeight - 0.5) * 10;
    vinyl.style.transform = `rotate(${Date.now() / 100 % 360}deg) translate(${mx}px, ${my}px)`;
});


/* ══════════════════════════════════════════════════════════════════
    🛠️ INTEGRATED ADMINISTRATIVE CATALOG & ASSET OPERATIONS
   ══════════════════════════════════════════════════════════════════ */

function adjustFileLabels() {
    const typeField = document.getElementById('media_type');
    if (!typeField) return;

    const selectedType = typeField.value;
    const titleLabel = document.getElementById('titleLabel');
    const artistLabel = document.getElementById('artistLabel');
    const fileLabel = document.getElementById('fileLabel');

    if (selectedType === 'movie') {
        if (titleLabel) titleLabel.textContent = 'FILM / SERIES TITLE';
        if (artistLabel) artistLabel.textContent = 'DIRECTOR / STUDIO';
        if (fileLabel) fileLabel.textContent = 'SELECT VIDEO FILE (.MP4/.MKV)';
    } else {
        if (titleLabel) titleLabel.textContent = 'TRACK TITLE';
        if (artistLabel) artistLabel.textContent = 'ARTIST / PRODUCER';
        if (fileLabel) fileLabel.textContent = 'SELECT AUDIO FILE (.MP3/.WAV)';
    }
}

async function submitUpload() {
    const uploadForm = document.getElementById('uploadForm');
    if (!uploadForm) return;

    const errorContainer = document.getElementById('uploadError');
    if (errorContainer) errorContainer.textContent = '';

    const payloadData = new FormData(uploadForm);

    try {
        const response = await fetch('/admin/upload', {
            method: 'POST',
            body: payloadData
        });

        if (response.redirected) {
            showToast("Asset successfully published!", "success");
            setTimeout(() => window.location.href = response.url, 1000);
            return;
        }

        const responseData = await response.json().catch(() => null);

        if (responseData && responseData.success) {
            showToast(`Successfully Published: ${responseData.title}`, 'success');
            setTimeout(() => window.location.href = '/admin', 1000);
        } else {
            if (errorContainer) {
                errorContainer.textContent = (responseData && responseData.error)
                    ? responseData.error
                    : 'A processing deployment error occurred or server redirected configuration.';
            }
        }
    } catch (exception) {
        console.error(exception);
        if (errorContainer) {
            errorContainer.textContent = 'Failed to process file allocations over the network stream layer.';
        }
    }
}

async function purgeMedia(itemId, itemTitle) {
    const userConfirmed = confirm(`⚠️ CRITICAL DATABASE OPERATION WARNING:\n\nAre you entirely sure you want to permanently delete "${itemTitle}" (ID: #${itemId})?\nThis action cannot be undone.`);
    if (!userConfirmed) return;

    try {
        const response = await fetch(`/admin/media/${itemId}/delete`, {
            method: 'POST'
        });
        const responseData = await response.json();

        if (responseData.success) {
            showToast(`Purged Array Node: ${itemTitle}`, 'success');

            const tableRow = document.getElementById(`media-row-${itemId}`);
            if (tableRow) {
                tableRow.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                tableRow.style.opacity = '0';
                tableRow.style.transform = 'translateX(-20px)';
                setTimeout(() => tableRow.remove(), 300);
            } else {
                setTimeout(() => window.location.reload(), 800);
            }
        } else {
            alert(responseData.error || "The database framework layer rejected the deletion execution stream.");
        }
    } catch (exception) {
        alert("Failed to communicate with administration network API router.");
    }
}

function calculateFileDuration(inputElement) {
    const file = inputElement.files[0];
    const durationInput = document.getElementById('durationInput');

    if (!file || !durationInput) return;

    durationInput.value = "Reading metadata...";

    const fileUrl = URL.createObjectURL(file);
    const mediaType = document.getElementById('media_type').value;
    const tempElement = document.createElement(mediaType === 'movie' ? 'video' : 'audio');

    tempElement.src = fileUrl;

    tempElement.addEventListener('loadedmetadata', () => {
        const totalSeconds = tempElement.duration;
        if (isNaN(totalSeconds)) {
            durationInput.value = "0:00";
            return;
        }

        const minutes = Math.floor(totalSeconds / 60);
        const seconds = Math.floor(totalSeconds % 60).toString().padStart(2, '0');

        durationInput.value = `${minutes}:${seconds}`;
        URL.revokeObjectURL(fileUrl);
    });

    tempElement.addEventListener('error', () => {
        durationInput.value = "Unknown Duration";
        URL.revokeObjectURL(fileUrl);
    });
}


// ─── HARDWARE MEDIA KEY INTEGRATION ───
if ('mediaSession' in navigator) {

    // Play button on keyboard
    navigator.mediaSession.setActionHandler('play', () => {
        if (!isPlaying) togglePlay();
    });

    // Pause button on keyboard
    navigator.mediaSession.setActionHandler('pause', () => {
        if (isPlaying) togglePlay();
    });

    // Optional: Next/Prev track support
    navigator.mediaSession.setActionHandler('previoustrack', () => {
        prevTrack();
    });

    navigator.mediaSession.setActionHandler('nexttrack', () => {
        nextTrack();
    });
}
