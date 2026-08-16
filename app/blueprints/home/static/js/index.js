// index.js — Home page: search autocomplete + find similar films
// Uses native fetch() — no jQuery required.

let selectedMovies = [];

// ─── Search autocomplete ─────────────────────────────────────────────────────

async function searchMovies(query) {
    const form = new FormData();
    form.append("movieName", query);
    const res = await fetch("/search_movies", { method: "POST", body: form });
    if (!res.ok) return [];
    return res.json();
}

document.getElementById("searchInput").addEventListener("keyup", async function () {
    const query = this.value.trim();
    const dropdown = document.getElementById("searchResults");

    if (!query) {
        dropdown.innerHTML = "";
        dropdown.classList.remove("show");
        return;
    }

    const movies = await searchMovies(query);
    dropdown.innerHTML = "";

    if (movies.length) {
        movies.forEach(movie => {
            const a = document.createElement("a");
            a.href = "#";
            a.className = "dropdown-item";
            a.dataset.title = movie.title;
            a.dataset.overview = movie.overview;
            a.dataset.vote = movie.vote_average;
            a.dataset.release = movie.release_date;
            a.dataset.poster = movie.poster_path;
            a.innerHTML = `
                <img src="https://image.tmdb.org/t/p/w200/${movie.poster_path}"
                     alt="${movie.title}" class="img-fluid"
                     style="max-width:40px; margin-right:10px;">
                ${movie.title}
            `;
            dropdown.appendChild(a);
        });
        dropdown.classList.add("show");
    } else {
        dropdown.classList.remove("show");
    }
});

// ─── Add selected film to the poster grid ────────────────────────────────────

document.addEventListener("click", function (e) {
    const item = e.target.closest("#searchResults .dropdown-item");
    if (item) {
        e.preventDefault();
        const title    = item.dataset.title;
        const poster   = item.dataset.poster;
        const overview = item.dataset.overview;
        const vote     = item.dataset.vote;
        const release  = item.dataset.release;

        if (!selectedMovies.some(m => m.title === title)) {
            selectedMovies.push({ title, poster });

            const div = document.createElement("div");
            div.className = "poster d-flex justify-content-center align-items-center bg-black position-relative";
            div.dataset.title    = title;
            div.dataset.overview = overview;
            div.dataset.vote     = vote;
            div.dataset.release  = release;
            div.dataset.poster   = poster;
            div.innerHTML = `
                <img src="https://image.tmdb.org/t/p/w200/${poster}"
                     alt="${title}" class="img-fluid mx-auto d-block">
                <button class="delete-btn position-absolute top-0 end-0 p-1 bg-dark text-white">
                    <i class="fa fa-times"></i>
                </button>
            `;
            document.querySelector(".search-results").appendChild(div);
        }

        document.getElementById("searchResults").classList.remove("show");
        return;
    }

    // Delete button
    const deleteBtn = e.target.closest(".delete-btn");
    if (deleteBtn) {
        const poster = deleteBtn.closest(".poster");
        const title = poster.dataset.title;
        selectedMovies = selectedMovies.filter(m => m.title !== title);
        poster.remove();
        return;
    }

    // Hide dropdown when clicking outside
    if (!e.target.closest(".dropdown")) {
        document.getElementById("searchResults").classList.remove("show");
    }
});

// ─── Find similar films ───────────────────────────────────────────────────────

async function findSimilarFilms(titles) {
    const form = new FormData();
    titles.forEach(t => form.append("movies[]", t));
    const res = await fetch("/find_similar_movies", { method: "POST", body: form });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.message || "Something went wrong. Please try again.");
        return;
    }
    window.location.href = "/discover";
}

document.getElementById("findSimilarMoviesBtn").addEventListener("click", function () {
    const titles = [...document.querySelectorAll(".search-results .poster")]
        .map(el => el.dataset.title)
        .filter(Boolean);

    if (!titles.length) {
        alert("Please select at least one film.");
        return;
    }
    findSimilarFilms(titles);
});
