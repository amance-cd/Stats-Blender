async function fetchGeneralStats(start_date="", end_date=""){
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/stats/general?start_date=${start_date}&end_date=${end_date}`);
        const data = await response.json();
        
        document.getElementById("listening-time").textContent = data.listening_time;
        document.getElementById("total-streams").textContent = data.total_plays;
        
    } catch (error) {
        console.error("Error:", error);    
    }
}

async function fetchTopTracks(limit=5, param=1, start_date="", end_date=""){
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/top/tracks?limit=${limit}&param=${param}&start_date=${start_date}&end_date=${end_date}`);
        const tracks = await response.json();
        
        const listElement = document.getElementById("top-tracks-list");
        
        //Empty the list to remove Loading... text
        listElement.innerHTML = "";
        
        tracks.forEach((track, index) => { //Loop over each song received
            const listItem = document.createElement("li"); //For each song, create a list item
            listItem.className = "grid-row tracks-grid";
            listItem.innerHTML = `
                <span class="col-rank">${index + 1}</span>
                <span class="col-title">${track.title}</span>
                <span class="col-artist">${track.artist}</span>
                <span class="col-plays">${track.play_count}</span>
                <span class="col-time">${track.listening_time}</span>
            `;
            listElement.appendChild(listItem); //Add it to the list
        });
        
    } catch (error) {
        console.error("Error: ", error);
    }
}


async function fetchTopArtists(limit=5, param=1, start_date="", end_date=""){
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/top/artists?limit=${limit}&param=${param}&start_date=${start_date}&end_date=${end_date}`);
        const artists = await response.json();
        
        const listElement = document.getElementById("top-artists-list");
        
        //Empty the list to remove Loading... text
        listElement.innerHTML = "";
        
        artists.forEach((artist, index) => { //Loop over each artist received
            const listItem = document.createElement("li"); //For each artist, create a list item
            listItem.className = "grid-row artists-grid";
            listItem.innerHTML = `
                <span class="col-rank">${index + 1}</span>
                <span class="col-artist">${artist.name}</span>
                <span class="col-plays">${artist.play_count}</span>
                <span class="col-time">${artist.listening_time}</span>
            `;
            listElement.appendChild(listItem); //Add it to the list
        });
        
    } catch (error) {
        console.error("Error: ", error);
    }
}

async function fetchTopAlbums(limit=5, param=1, start_date="", end_date=""){
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/top/albums?limit=${limit}&param=${param}&start_date=${start_date}&end_date=${end_date}`);
        const albums = await response.json();
        
        const listElement = document.getElementById("top-albums-list");
        
        //Empty the list to remove Loading... text
        listElement.innerHTML = "";
        
        albums.forEach((album, index) => { //Loop over each album received
            const listItem = document.createElement("li"); //For each album, create a list item
            listItem.className = "grid-row albums-grid";
            listItem.innerHTML = `
                <span class="col-rank">${index + 1}</span>
                <span class="col-album">${album.album}</span>
                <span class="col-artist">${album.artist}</span>
                <span class="col-plays">${album.play_count}</span>
                <span class="col-time">${album.listening_time}</span>
            `;
            listElement.appendChild(listItem); //Add it to the list
        });
        
    } catch (error) {
        console.error("Error: ", error);
    }
}



let limits = { tracks: 5, artists: 5, albums: 5 };

fetchGeneralStats("2025-01-01", "2026-01-01");
fetchTopTracks(limits.tracks, 0);
fetchTopArtists(limits.artists, 0);
fetchTopAlbums(limits.albums, 0);

//Filters button
document.getElementById("apply-btn").addEventListener("click", () => {
    //Read values from the inputs
    const param = document.getElementById("sort-param").value;
    const startDate = document.getElementById("start-date").value;
    const endDate = document.getElementById("end-date").value;
    
    //Call our API functions again with new values
    fetchGeneralStats(startDate, endDate);
    fetchTopTracks(limits.tracks, param, startDate, endDate);
    fetchTopArtists(limits.artists, param, startDate, endDate);
    fetchTopAlbums(limits.albums, param, startDate, endDate);
});

// See more buttons
document.getElementById("more-tracks-btn").addEventListener("click", () => {
    limits.tracks += 5; // Add 5 more items
    const param = document.getElementById("sort-param").value;
    const sd = document.getElementById("start-date").value;
    const ed = document.getElementById("end-date").value;
    fetchTopTracks(limits.tracks, param, sd, ed);
});

document.getElementById("more-artists-btn").addEventListener("click", () => {
    limits.artists += 5;
    const param = document.getElementById("sort-param").value;
    const sd = document.getElementById("start-date").value;
    const ed = document.getElementById("end-date").value;
    fetchTopArtists(limits.artists, param, sd, ed);
});

document.getElementById("more-albums-btn").addEventListener("click", () => {
    limits.albums += 5;
    const param = document.getElementById("sort-param").value;
    const sd = document.getElementById("start-date").value;
    const ed = document.getElementById("end-date").value;
    fetchTopAlbums(limits.albums, param, sd, ed);
});
