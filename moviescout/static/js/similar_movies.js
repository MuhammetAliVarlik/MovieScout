// similar_movies.js

var animating = false;
var cardsCounter = 0;
var numOfCards = 10;
var decisionVal = 80;
var pullDeltaX = 0;
var deg = 0;
var $card, $cardReject, $cardLike;

// Function to update the card's position and opacity
function pullChange() {
    animating = true;
    deg = pullDeltaX / 10;
    $card.css("transform", "translateX(" + pullDeltaX + "px) rotate(" + deg + "deg)");

    var opacity = pullDeltaX / 100;
    var rejectOpacity = (opacity >= 0) ? 0 : Math.abs(opacity);
    var likeOpacity = (opacity <= 0) ? 0 : opacity;
    $cardReject.css("opacity", rejectOpacity);
    $cardLike.css("opacity", likeOpacity);
}

// Function to release the card after the user swipes it
function release() {
    if (pullDeltaX >= decisionVal) {
        $card.addClass("to-right");

        // Collect movie details from data attributes
        const movieDetails = {
            title: $card.data("movie-title"),
            similarity_score: $card.data("movie-similarity"), 
            release_date: $card.data("movie-release"),
            genres: $card.data("movie-genres"),
            overview: $card.data("movie-overview"),
            poster_path: $card.data("movie-poster"),
            vote_average: $card.data("movie-vote")
        };

        // Check if the movie already exists in the likedMovies array
        const isMovieLiked = likedMovies.some(movie => movie.title === movieDetails.title);

        if (!isMovieLiked) {
            // Add the movie to the list if not already liked
            likedMovies.push(movieDetails);
            // Store likedMovies list in localStorage
            saveLikedMovies();
            updateLikedMoviesCount(likedMovies);
            updateLikedMoviesList(likedMovies);

            
        }
    } else if (pullDeltaX <= -decisionVal) {
        $card.addClass("to-left");
    }

    if (Math.abs(pullDeltaX) >= decisionVal) {
        $card.addClass("inactive");

        setTimeout(function() {
            $card.addClass("below").removeClass("inactive to-left to-right");
            cardsCounter++;
            if (cardsCounter === numOfCards) {
                cardsCounter = 0;
                $(".demo__card").removeClass("below");

                // When all cards are swiped, show the end of recommendations modal
                $('#endOfRecommendationsModal').modal('show');
            }
        }, 300);
    }

    if (Math.abs(pullDeltaX) < decisionVal) {
        $card.addClass("reset");
    }

    setTimeout(function() {
        $card.attr("style", "").removeClass("reset")
            .find(".demo__card__choice").attr("style", "");

        pullDeltaX = 0;
        animating = false;
    }, 300);
}

$(document).on("mousedown touchstart", ".demo__card:not(.inactive)", function(e) {
    if (animating) return;

    $card = $(this);
    $cardReject = $(".demo__card__choice.m--reject", $card);
    $cardLike = $(".demo__card__choice.m--like", $card);
    var startX = e.pageX || e.originalEvent.touches[0].pageX;

    $(document).on("mousemove touchmove", function(e) {
        var x = e.pageX || e.originalEvent.touches[0].pageX;
        pullDeltaX = (x - startX);
        if (!pullDeltaX) return;
        pullChange();
    });

    $(document).on("mouseup touchend", function() {
        $(document).off("mousemove touchmove mouseup touchend");
        if (!pullDeltaX) return; // prevents from rapid click events
        release();
    });
});
