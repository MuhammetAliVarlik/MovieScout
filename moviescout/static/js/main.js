// Function to save the likedMovies to localStorage
function saveLikedMovies() {
    console.log(likedMovies);
    localStorage.setItem("likedMovies", JSON.stringify(likedMovies));
}

// Function to load the likedMovies from localStorage
function loadLikedMovies() {
    const likedMoviesData = localStorage.getItem("likedMovies");

    if (likedMoviesData) {
        try {
            // JSON verisini çözümle
            const parsedData = JSON.parse(likedMoviesData);

            // Eğer verinin türü bir dizi ise, döndür
            if (Array.isArray(parsedData)) {
                return parsedData;
            } else {
                console.warn("Beklenen dizi formatında veri gelmedi:", parsedData);
                return [];  // Hatalı veri formatı durumunda boş bir dizi döndür
            }
        } catch (error) {
            console.error("Veri çözümleme hatası:", error);
            return [];  // JSON çözümleme hatasında boş dizi döndür
        }
    }

    return [];  // Eğer hiç veri yoksa boş bir dizi döndür
}



// Function to update the likedMovies count in the navbar
function updateLikedMoviesCount(likedMovies) {
    $("#likedMoviesCount").text(likedMovies.length);
    console.log(likedMovies.length);
}

// Function to render the liked movies list in the modal
function updateLikedMoviesList(likedMovies) {
    const $likedMoviesList = $("#likedMoviesList");
    $likedMoviesList.empty(); // Clear the list

    // Loop through each liked movie and append it to the list
    likedMovies.forEach(function(movie) {
        $likedMoviesList.append(`
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

$(document).ready(function () {
    // Load liked movies from localStorage
    likedMovies = loadLikedMovies();  // Don't redeclare `likedMovies` here
    if (likedMovies && likedMovies.length > 0) {
        console.log("Loaded liked movies from localStorage:", likedMovies);
        updateLikedMoviesCount(likedMovies); // Pass likedMovies to the update function
        updateLikedMoviesList(likedMovies);  // Pass likedMovies to the update function
    }
});
