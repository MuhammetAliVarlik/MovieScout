// main.js — shared across every page: liked-movies list, movie-details modal,
// and the Letterboxd import modal. Vanilla JS: no jQuery required.

let likedMovies = [];

// ─── Liked movies (localStorage) ───────────────────────────────────────────────

function saveLikedMovies() {
    localStorage.setItem("likedMovies", JSON.stringify(likedMovies));
}

function loadLikedMovies() {
    const raw = localStorage.getItem("likedMovies");
    if (!raw) return [];
    try {
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
        console.error("Failed to parse likedMovies from localStorage:", error);
        return [];
    }
}

function updateLikedMoviesCount(movies) {
    const el = document.getElementById("likedMoviesCount");
    if (el) el.textContent = movies.length;
}

function updateLikedMoviesList(movies) {
    const list = document.getElementById("likedMoviesList");
    if (!list) return;
    list.innerHTML = "";
    movies.forEach(movie => {
        list.insertAdjacentHTML("beforeend", `
            <div class="liked-movie-card bg-dark text-white p-3 rounded mb-3">
                <div class="d-flex align-items-center">
                    <img src="https://image.tmdb.org/t/p/w200/${movie.poster_path}" class="img-fluid rounded me-3" style="width: 100px;">
                    <div>
                        <h5 class="fw-bold mb-1">${movie.title}</h5>
                        <p class="mb-1">${movie.release_date} | ${movie.genres}</p>
                        <p class="mb-1">Rating: ${movie.vote_average} / 10 (${movie.vote_average / 2} stars)</p>
                    </div>
                </div>
                <p class="mt-3" style="font-size: 0.9rem;">${movie.overview}</p>
            </div>
        `);
    });
}

function copyLikedMoviesToWhatsApp(movies) {
    let message = "Here are my liked movies:\n\n";
    movies.forEach((movie, index) => {
        message += `${index + 1}. ${movie.title} (${movie.release_date})\n`;
        message += `   Genres: ${movie.genres}\n`;
        message += `   Rating: ${movie.vote_average} / 10\n`;
        message += `   Overview: ${movie.overview}\n\n`;
    });
    navigator.clipboard.writeText(message)
        .then(() => alert("Movies copied to clipboard! Paste it in WhatsApp."))
        .catch(err => {
            console.error("Error copying text:", err);
            alert("Failed to copy text.");
        });
}

document.addEventListener("click", function (e) {
    if (e.target.closest("#copyToWhatsApp")) {
        copyLikedMoviesToWhatsApp(likedMovies);
    }
});

document.addEventListener("DOMContentLoaded", function () {
    likedMovies = loadLikedMovies();
    if (likedMovies.length > 0) {
        updateLikedMoviesCount(likedMovies);
        updateLikedMoviesList(likedMovies);
    }
    refreshTasteProfilePill();
});

// ─── Taste profile pill (navbar) ────────────────────────────────────────────────

async function refreshTasteProfilePill() {
    const pill = document.getElementById("tasteProfilePill");
    if (!pill) return;
    try {
        const res = await fetch("/api/profile");
        const data = await res.json();
        if (data.total_films > 0) {
            pill.textContent = `🎬 ${data.total_films} film${data.total_films === 1 ? "" : "s"} imported`;
            pill.classList.add("has-profile");
            pill.style.display = "";
        }
    } catch (err) {
        console.error("Failed to load taste profile:", err);
    }
}

// ─── Movie details modal ────────────────────────────────────────────────────────

document.addEventListener("click", function (e) {
    const card = e.target.closest(".poster");
    if (!card) return;
    const d = card.dataset;

    document.getElementById("modal-title").textContent = d.title;
    document.getElementById("modal-poster").src = `https://image.tmdb.org/t/p/w200/${d.poster}`;
    document.getElementById("modal-overview").textContent = d.overview;
    document.getElementById("modal-vote").textContent = d.vote;
    document.getElementById("modal-release-date").textContent = d.release;
    document.getElementById("modal-genres").textContent = d.genres;

    new bootstrap.Modal(document.getElementById("movieModal")).show();
});

// ─── Letterboxd import ───────────────────────────────────────────────────────────

document.addEventListener("submit", async function (e) {
    const form = e.target.closest("#importLetterboxdForm");
    if (!form) return;
    e.preventDefault();

    const fileInput = document.getElementById("letterboxdFile");
    const resultEl = document.getElementById("importResult");
    const submitBtn = form.querySelector("button[type=submit]");

    if (!fileInput.files.length) {
        resultEl.innerHTML = `<div class="text-danger">Choose a .zip or .csv file first.</div>`;
        return;
    }

    const body = new FormData();
    body.append("file", fileInput.files[0]);

    submitBtn.disabled = true;
    resultEl.innerHTML = `<div class="text-muted">Importing…</div>`;

    try {
        const res = await fetch("/api/import", { method: "POST", body });
        const data = await res.json();
        if (!res.ok) {
            resultEl.innerHTML = `<div class="text-danger">${data.error || "Import failed."}</div>`;
            return;
        }
        const genres = (data.top_genres || []).join(", ") || "—";
        const films = (data.top_films || []).map(f => `${f.title} (${f.rating}★)`).join(", ") || "—";
        resultEl.innerHTML = `
            <div class="text-success mb-2">Imported ${data.total_films} film(s).</div>
            <div class="small text-muted">Top genres: ${genres}</div>
            <div class="small text-muted">Top rated: ${films}</div>
            <div class="small text-white mt-2">Building your recommendations…</div>
        `;
        refreshTasteProfilePill();
        await seedRecommendationsFromProfile(data.top_films || [], resultEl);
    } catch (err) {
        console.error("Letterboxd import failed:", err);
        resultEl.innerHTML = `<div class="text-danger">Something went wrong. Please try again.</div>`;
    } finally {
        submitBtn.disabled = false;
    }
});

async function seedRecommendationsFromProfile(topFilms, resultEl) {
    const titles = topFilms.map(f => f.title).filter(Boolean);
    if (!titles.length) {
        resultEl.insertAdjacentHTML("beforeend", `
            <div class="small text-muted mt-2">None of your imported films matched closely enough to seed recommendations automatically — try searching for one you love on the Home page instead.</div>
        `);
        return;
    }

    const seedForm = new FormData();
    titles.forEach(t => seedForm.append("movies[]", t));

    try {
        const res = await fetch("/find_similar_movies", { method: "POST", body: seedForm });
        const data = await res.json();
        if (res.ok && data.total > 0) {
            window.location.href = "/discover";
            return;
        }
        resultEl.insertAdjacentHTML("beforeend", `
            <div class="small text-muted mt-2">We couldn't find enough similar films locally to build a feed yet — try searching for a film you love on the Home page instead.</div>
        `);
    } catch (err) {
        console.error("Auto-recommendation from taste profile failed:", err);
        resultEl.insertAdjacentHTML("beforeend", `
            <div class="small text-danger mt-2">Couldn't build recommendations automatically. Try searching for a film on the Home page instead.</div>
        `);
    }
}
