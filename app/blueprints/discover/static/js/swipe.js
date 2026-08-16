// swipe.js — Card-swipe discovery interface
// Vanilla JS: no jQuery required.

let animating = false;
let cardsCounter = 0;
const decisionVal = 80;
let pullDeltaX = 0;
let activeCard = null;
let cardReject = null;
let cardLike = null;

// ─── Card transform helpers ──────────────────────────────────────────────────

function pullChange() {
    animating = true;
    const deg = pullDeltaX / 10;
    activeCard.style.transform = `translateX(${pullDeltaX}px) rotate(${deg}deg)`;
    const opacity = pullDeltaX / 100;
    if (cardReject) cardReject.style.opacity = opacity >= 0 ? 0 : Math.abs(opacity);
    if (cardLike)   cardLike.style.opacity   = opacity <= 0 ? 0 : opacity;
}

function release() {
    if (pullDeltaX >= decisionVal) {
        activeCard.classList.add("to-right");
        saveToWatchlist(activeCard);
    } else if (pullDeltaX <= -decisionVal) {
        activeCard.classList.add("to-left");
    }

    if (Math.abs(pullDeltaX) >= decisionVal) {
        activeCard.classList.add("inactive");
        setTimeout(() => {
            activeCard.classList.add("below");
            activeCard.classList.remove("inactive", "to-left", "to-right");
            activeCard.removeAttribute("style");
            cardsCounter++;
            const allCards = document.querySelectorAll(".demo__card").length;
            if (cardsCounter === allCards) {
                cardsCounter = 0;
                document.querySelectorAll(".demo__card").forEach(c => c.classList.remove("below"));
                const endModal = document.getElementById("endOfRecommendationsModal");
                if (endModal) new bootstrap.Modal(endModal).show();
            }
        }, 300);
    }

    if (Math.abs(pullDeltaX) < decisionVal) {
        activeCard.classList.add("reset");
    }

    setTimeout(() => {
        if (activeCard) {
            activeCard.removeAttribute("style");
            activeCard.classList.remove("reset");
            if (cardReject) cardReject.removeAttribute("style");
            if (cardLike)   cardLike.removeAttribute("style");
        }
        pullDeltaX = 0;
        animating = false;
    }, 300);
}

// ─── Watchlist ────────────────────────────────────────────────────────────────

function saveToWatchlist(card) {
    const d = card.dataset;
    const film = { title: d.title, similarity_score: d.similarity,
        release_date: d.release, genres: d.genres,
        overview: d.overview, poster_path: d.poster, vote_average: d.vote };
    if (!likedMovies.some(m => m.title === film.title)) {
        likedMovies.push(film);
        saveLikedMovies();
        updateLikedMoviesCount(likedMovies);
        updateLikedMoviesList(likedMovies);
    }
}

// ─── Drag / touch ─────────────────────────────────────────────────────────────

document.addEventListener("mousedown", startDrag);
document.addEventListener("touchstart", startDrag, { passive: true });

function startDrag(e) {
    const card = e.target.closest(".demo__card:not(.inactive)");
    if (!card || animating) return;

    activeCard = card;
    cardReject = card.querySelector(".demo__card__choice.m--reject");
    cardLike   = card.querySelector(".demo__card__choice.m--like");
    const startX = e.touches ? e.touches[0].pageX : e.pageX;

    const onMove = ev => {
        pullDeltaX = (ev.touches ? ev.touches[0].pageX : ev.pageX) - startX;
        if (pullDeltaX) pullChange();
    };
    const onEnd = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("touchmove", onMove);
        document.removeEventListener("mouseup", onEnd);
        document.removeEventListener("touchend", onEnd);
        if (pullDeltaX) release();
    };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("touchmove", onMove, { passive: true });
    document.addEventListener("mouseup", onEnd);
    document.addEventListener("touchend", onEnd);
}

// ─── Keyboard navigation ──────────────────────────────────────────────────────

document.addEventListener("keydown", e => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const card = document.querySelector(".demo__card:not(.inactive):not(.below)");
    if (!card) return;
    activeCard = card;
    cardReject = card.querySelector(".demo__card__choice.m--reject");
    cardLike   = card.querySelector(".demo__card__choice.m--like");
    pullDeltaX = e.key === "ArrowRight" ? decisionVal + 1 : -(decisionVal + 1);
    release();
});
