
// Array to keep track of selected movies
let selectedMovies = [];

// Handle typing in the search input field and make an AJAX request
$('#searchInput').on('keyup', function () 
{
    const movieName = $(this).val();
    if (movieName.length === 0) 
    {
        $('#searchResults').empty().removeClass('show');
        return;
    }

    $.ajax(
    {
        url: '/search_movies', // Flask API endpoint
        type: 'POST',
        data: { movieName: movieName },
        success: function (response) 
        {
            const dropdown = $('#searchResults');
            dropdown.empty(); // Clear previous results

            if (response.length) 
            {
                // Create dropdown items dynamically for each movie result
                response.forEach(movie => {
                    dropdown.append(`
                        <a href="#" class="dropdown-item" data-title="${movie.title}" data-poster="${movie.poster_path}">
                            <img src="https://image.tmdb.org/t/p/w200/${movie.poster_path}" alt="${movie.title}" class="img-fluid" style="max-width: 40px; margin-right: 10px;">
                            ${movie.title}
                        </a>
                    `);
                });
                dropdown.addClass('show'); // Show dropdown
            } else 
            {
                dropdown.removeClass('show'); // Hide if no results
            }
        },
        error: function (error) {
            console.log('Error:', error);
        }
    });
});

// Handle click on a dropdown item
$(document).on('click', '#searchResults .dropdown-item', function (e) 
{
    e.preventDefault();  // Prevent the default action

    const title = $(this).data('title');
    const posterUrl = $(this).data('poster');

    // Check if the movie is already in the selectedMovies array to avoid duplicates
    if (!selectedMovies.some(movie => movie.title === title)) 
    {
        // Add movie details to the selectedMovies array
        selectedMovies.push({ title: title, poster: posterUrl });

        // Add the movie poster to the search-results section
        const movieHtml = `
            <div class="poster d-flex justify-content-center align-items-center bg-black position-relative" data-title="${title}">
                <img src="https://image.tmdb.org/t/p/w200/${posterUrl}" alt="${title}" class="img-fluid mx-auto d-block">
                <!-- Delete button -->
                <button class="delete-btn position-absolute top-0 end-0 p-1 bg-dark text-white">
                    <i class="fa fa-times"></i>
                </button>
            </div>
        `;
        $('.search-results').append(movieHtml); // Append to the search-results section
    }
});

// Handle removal of poster on delete button click
$(document).on('click', '.delete-btn', function () 
{
    const title = $(this).closest('.poster').data('title');

    // Remove the movie from selectedMovies array
    selectedMovies = selectedMovies.filter(movie => movie.title !== title);

    // Remove the poster container from the DOM
    $(this).closest('.poster').remove();
});

// Hide dropdown if clicked outside
$(document).on('click', function (e) 
{
    if (!$(e.target).closest('.dropdown').length) 
    {
        $('#searchResults').removeClass('show');
    }
});

// Example: Log the selectedMovies array to the console to see the current list
// You can replace this with any other action as needed
$('#findSimilarMoviesBtn').on('click', function() 
{
    console.log("Selected Movies:", selectedMovies);
});


$('#findSimilarMoviesBtn').on('click', function () 
{
    // Array to hold the titles of selected movies
    const movieIds = [];

    // Iterate over each selected movie in the search results
    $('.search-results .poster').each(function () 
    {
        const movieTitle = $(this).data('title');  // Get the movie title
        movieIds.push(movieTitle);  // Add the title to the movieIds array
    });

    // Check if we have selected any movies
    if (movieIds.length === 0) 
    {
        alert("Please select at least one movie.");
        return;
    }

    // Make an AJAX request to find similar movies
    $.ajax(
    {
        url: '/find_similar_movies',
        type: 'POST',
        data: { 'movies[]': movieIds },  // Send selected movie titles as an array
        traditional: true,  // Ensures array is sent in correct format
        success: function(response) 
        {
            // If request is successful, redirect or update the page
            window.location.href = '/similar_movies'; // Or handle the response as needed
        },
        error: function(error) 
        {
            console.log('Error:', error);
        }
    });
});
