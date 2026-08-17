// chat.js — AI film chat frontend
// Streams responses from /chat/stream using fetch() + ReadableStream.
// After streaming ends, extracts film titles from the response and
// fetches TMDB cards via /chat/search for each one.
//
// Saved films go into the same `likedMovies` list main.js manages (shared
// with the Discover swipe deck and the Home search grid), not a separate
// list — otherwise a film liked here would never show up anywhere else.

// ─── Message sending ──────────────────────────────────────────────────────────

async function sendMessage(message) {
    appendBubble("user", message);
    const typingBubble = appendBubble("assistant", "", "typing");

    const form = new FormData();
    form.append("message", message);

    let fullText = "";

    try {
        const res = await fetch("/chat/stream", { method: "POST", body: form });
        if (!res.ok) throw new Error(await res.text());

        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const raw = decoder.decode(value, { stream: true });
            // Each SSE line: "data: <token>\n\n"
            for (const line of raw.split("\n")) {
                if (!line.startsWith("data: ")) continue;
                const token = line.slice(6);
                if (token === "[DONE]") break;
                fullText += token;
            }
            typingBubble.classList.remove("typing");
            typingBubble.innerHTML = formatTextContent(fullText);
        }
    } catch (err) {
        typingBubble.classList.remove("typing");
        typingBubble.textContent = "⚠️ Could not reach the AI. Is the LLM model downloaded?";
        return;
    }

    // Extract film titles (anything enclosed in "double quotes") and fetch cards
    const titles = extractFilmTitles(fullText);
    if (titles.length) {
        const cardContainer = document.createElement("div");
        cardContainer.className = "d-flex flex-wrap gap-2 mt-2";
        typingBubble.insertAdjacentElement("afterend", cardContainer);
        await Promise.all(titles.map(t => fetchAndAppendFilmCard(t, cardContainer)));
    }
}

document.getElementById("chatInput").addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        const msg = this.value.trim();
        if (msg) {
            this.value = "";
            sendMessage(msg);
        }
    }
});

// ─── Film card fetching ────────────────────────────────────────────────────────

async function fetchAndAppendFilmCard(title, container) {
    const form = new FormData();
    form.append("title", title);
    const res = await fetch("/chat/search", { method: "POST", body: form });
    if (!res.ok) return;
    const film = await res.json();
    if (!film) return;
    const el = document.createElement("div");
    el.innerHTML = buildFilmCard(film);
    container.appendChild(el.firstElementChild);
}

function buildFilmCard(film) {
    const poster = film.poster_path
        ? `https://image.tmdb.org/t/p/w200/${film.poster_path}`
        : "/static/img/no-poster.png";
    const year = film.release_date ? film.release_date.slice(0, 4) : "";

    return `
        <div class="film-card bg-black rounded-3 p-2 text-white" style="width:140px; cursor:pointer;"
             data-movie-title="${escapeAttr(film.title)}"
             data-movie-overview="${escapeAttr(film.overview)}"
             data-movie-vote="${film.vote_average}"
             data-movie-release="${film.release_date || ''}"
             data-movie-poster="${film.poster_path || ''}"
             data-movie-genres="${escapeAttr(film.genres || '')}">
            <img src="${poster}" alt="${escapeAttr(film.title)}"
                 class="img-fluid rounded-2 mb-2" style="width:100%;">
            <p class="mb-1 fw-bold" style="font-size:0.75rem;">${film.title}</p>
            <p class="mb-1 text-muted" style="font-size:0.7rem;">${year}</p>
            <div class="d-flex gap-1">
                <button class="btn btn-sm btn-light w-100 save-film-btn">❤</button>
                <a href="${film.letterboxd_url}"
                   target="_blank" rel="noopener noreferrer"
                   class="btn btn-sm btn-outline-light w-100">LB</a>
            </div>
        </div>
    `;
}

// ─── Watchlist ─────────────────────────────────────────────────────────────────

document.addEventListener("click", function (e) {
    const btn = e.target.closest(".save-film-btn");
    if (!btn) return;
    const card = btn.closest(".film-card");
    if (!card) return;
    const film = {
        title:        card.dataset.movieTitle,
        overview:     card.dataset.movieOverview,
        vote_average: card.dataset.movieVote,
        release_date: card.dataset.movieRelease,
        poster_path:  card.dataset.moviePoster,
        genres:       card.dataset.movieGenres,
    };
    if (!likedMovies.some(m => m.title === film.title)) {
        likedMovies.push(film);
        saveLikedMovies();
        updateLikedMoviesCount(likedMovies);
        updateLikedMoviesList(likedMovies);
        btn.textContent = "✓";
        btn.disabled = true;
    }
});

// ─── Helpers ───────────────────────────────────────────────────────────────────

function appendBubble(role, content, extraClass = "") {
    const container = document.getElementById("chatContainer");
    const div = document.createElement("div");
    div.className = `chat-bubble ${role === "user" ? "a1" : "a2"} ${extraClass}`.trim();
    if (extraClass === "typing") {
        div.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
    } else {
        div.innerHTML = content;
    }
    container.appendChild(div);
    div.scrollIntoView({ behavior: "smooth", block: "end" });
    return div;
}

function extractFilmTitles(text) {
    const matches = text.match(/"([^"]+)"/g) || [];
    return [...new Set(matches.map(m => m.replace(/"/g, "").trim()))].filter(Boolean);
}

function formatTextContent(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"([^"]+)"/g, '<strong>"$1"</strong>')
        .replace(/\n/g, "<br>");
}

function escapeAttr(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}
