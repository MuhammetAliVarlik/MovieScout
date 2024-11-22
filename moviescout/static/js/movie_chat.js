function addMoviesToList(button)
    {   var $button=$(button);
        const movieDetails = {
            title: $button.data("movie-title"),
            similarity_score: $button.data("movie-similarity"), 
            release_date: $button.data("movie-release"),
            genres: $button.data("movie-genres"),
            overview: $button.data("movie-overview"),
            poster_path: $button.data("movie-poster"),
            vote_average: $button.data("movie-vote")
        };
        const isMovieLiked = likedMovies.some(movie => movie.title === movieDetails.title);

        if (!isMovieLiked) {
            // Add the movie to the list if not already liked
            likedMovies.push(movieDetails);
            // Store likedMovies list in localStorage
            saveLikedMovies();
            updateLikedMoviesCount(likedMovies);
            updateLikedMoviesList(likedMovies);

            
        }
    };

$(document).ready(function () 
{
    // Array to keep track of selected movies
    var movieName=[];
    var final_chunk="";

    // Handle typing in the search input field and make an AJAX request
    $('#chatInput').on('keydown', function (event) 
    {
        if (event.keyCode === 13) // Enter key
        {  
            event.preventDefault(); // Prevent form submission
            const movieChat = $(this).val(); // Get the input value

            if (movieChat.trim() !== "") // Check if input is not empty 
            { 
                // Add user's message to the chat container
                $('#chatContainer').append(`
                    <div class="chat-bubble a1">
                        ${movieChat}
                    </div>
                `);
                $('#chatContainer').append(`
                    <div class="chat-bubble a2 typing">
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                `);

                // Clear the input field after sending the message
                $(this).val('');

                // Make AJAX request to the server
                $.ajax(
                {
                        url: '/chat_movies', // Flask endpoint
                        type: 'POST',
                        data: { movieChat: movieChat },
                        xhrFields: {
                            onprogress: function (e) 
                            {
                                
                                // Get the response text from the stream
                                const chunk = e.target.responseText;
                                let formattedContent = formatTextContent(chunk);
                                final_chunk=formattedContent;
                                // Update the chat container with the streamed chunk
                                $('#chatContainer .chat-bubble.a2').last().html(formattedContent); // Update the last response bubble
                            }
                    },
                    success: function (response) 
                    {
                        movieName = extractMovieTitles(final_chunk); // Film başlıklarını çıkartıyoruz
                        console.log(movieName);

                        // Eklenen filmleri tutacak bir dizi
                        let addedMovies = [];

                        if (movieName && movieName.length > 0) 
                        {
                            // Her bir film adı için tek tek AJAX isteği gönderiyoruz
                            movieName.forEach(function (movie) 
                            {
                                $.ajax(
                                    {
                                        url: '/search_chat_movies', // Flask API endpoint
                                        type: 'POST',
                                        data: { movieName: movie }, // Tek bir film adı ile istek gönderiyoruz
                                        success: function (response) 
                                        {
                                            console.log(response);
                                            // Dönen her bir film için HTML içeriği oluşturuyoruz
                                            response.forEach(function (movie) 
                                            {
                                                // Eğer film zaten eklenmemişse
                                                if (!addedMovies.includes(movie.title)) 
                                                {
                                                    // Eklenmiş filmleri diziye ekle
                                                    addedMovies.push(movie.title);

                                                    // HTML içeriği oluştur ve ekle
                                                    $('#chatContainer .chat-bubble.a2').last().append(
                                                    `<div class="liked-movie-card bg-dark text-white p-3 rounded mb-3">
                                                        <div class="d-flex align-items-center">
                                                            <img src="https://image.tmdb.org/t/p/w200/${movie.poster_path}" class="img-fluid rounded me-3" style="width: 100px;">
                                                            <div>
                                                                <h5 class="fw-bold mb-1">${movie.title}</h5>
                                                                <p class="mb-1">${movie.release_date} | ${movie.genres}</p>
                                                                <p class="mb-1">Rating: ${movie.vote_average} / 10 (${movie.vote_average / 2} stars)</p>
                                                            </div>
                                                        </div>
                                                        
                                                        <p class="mt-3" style="font-size: 0.9rem;">${movie.overview}</p>

                                                        <!-- Like Button -->
                                                        <button class="like-btn btn btn-outline-light mt-2" 
                                                                data-movie-title="${movie.title}" 
                                                                data-movie-similarity="${movie.similarity_score}" 
                                                                data-movie-release="${movie.release_date}" 
                                                                data-movie-genres="${movie.genres}" 
                                                                data-movie-overview="${movie.overview}" 
                                                                data-movie-poster="${movie.poster_path}" 
                                                                data-movie-vote="${movie.vote_average}" 
                                                                onclick="addMoviesToList(this)">
                                                            <i class="fa fa-thumbs-up"></i> Like
                                                        </button>

                                                    </div>`
                                                    );

                                                }
                                            });
                                        },
                                        error: function (error) 
                                        {
                                            console.log('Error:', error); // Hata durumunda konsola yaz
                                        }
                                    });
                            });
                        }
                        final_chunk = ""; // final_chunk'i sıfırlıyoruz
                    },
                    error: function (error) 
                    {
                        console.log('Error:', error); // Handle error
                    }
                });
                    
            }
        }
    });

    // Function to format the received chunk into HTML with headings and paragraphs
    function formatTextContent(data) {
        let result = data;
        // 1. ve 2. gibi numaralandırmalar için <li> ile sarma
        result = result.replace(/^(\d+\.\s+)(.*)$/gm, '<li>$2</li>');
        
        // ** Some text ** gibi ifadeleri <h4> ile sarmak
        result = result.replace(/\*\*([^\*]+)\*\*/g, '<h4>$1</h4>');
        
        // - Some text gibi ifadeleri <ul> ile sarmak
        result = result.replace(/^- (.*)$/gm, '<ul><li>$1</li></ul>');
        
        // Diğer metinleri <p> ile sarmak
        result = result.replace(/^(?!<)(.*)$/gm, '<p>$1</p>');
        
        return result;
    }

    function extractMovieTitles(inputText) {
        // Farklı tırnak işaretlerini destekleyen regex
        const regex = /["“”‘’*]{2}([^"“”‘’*]+)["“”‘’*]{2}\s?\(\d{4}\)|["“”‘’]([^"“”‘’]+)["“”‘’]\s?\(\d{4}\)|["“”‘’*]{2}([^"“”‘’*]+)["“”‘’*]{2}|["“”‘’]([^"“”‘’]+)/g;
        let matches = [];
        let match;
        
        // Regex ile metinde eşleşmeleri bul
        while ((match = regex.exec(inputText)) !== null) {
            if (match[1]) {
                // Çift yıldız ve yıl olan
                matches.push(match[1]);
            } else if (match[2]) {
                // Tırnak ve yıl olan
                matches.push(match[2]);
            } else if (match[3]) {
                // Sadece çift yıldız olan
                matches.push(match[3]);
            } else if (match[4]) {
                // Sadece tırnak olan
                matches.push(match[4]);
            }
        }
        
        return matches;
    }


});