function rankClass(i) {
    if (i === 0) return "top-1";
    if (i === 1) return "top-2";
    if (i === 2) return "top-3";
    return "";
}

function slugify(text) {
  return text.toString().toLowerCase()
    .replace(/\s+/g, '-')           // Replace spaces with -
    .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
    .replace(/\-\-+/g, '-')         // Replace multiple - with single -
    .replace(/^-+/, '')             // Trim - from start of text
    .replace(/-+$/, '');            // Trim - from end of text
}

let currentPage = "dashboard";
let previousPage = "dashboard";

//Helper: split "Artist1, Artist2" into clickable links
function makeArtistLinks(artistStr) {
    if (!artistStr) return "";
    return artistStr.split(", ").map(name => 
        `<span class="clickable artist-name" onclick="openArtistPage('${name.replace(/'/g, "\\'")}')">${name}</span>`
    ).join(", ");
}

//Helper: render a stats grid
function renderStatGrid(stats) {
    if (!stats) return "";
    return `
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Plays</div>
                <div class="stat-value">${stats.total_plays.toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Time</div>
                <div class="stat-value">${stats.listening_time}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Tracks</div>
                <div class="stat-value">${stats.unique_tracks.toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">First Listen</div>
                <div class="stat-value">${stats.first_listen || "N/A"}</div>
            </div>
        </div>
    `;
}

//Open a pinned artist detail page
async function openArtistPage(name) {
    const pageId = `artist-${slugify(name)}`;
    
    let pageDiv = document.getElementById(`page-${pageId}`);
    
    if (pageDiv) {
        navigateTo(pageId);
        return;
    }
    
    pageDiv = document.createElement("div");
    pageDiv.id = `page-${pageId}`;
    pageDiv.className = "page";
    pageDiv.innerHTML = `<h1 class="section-title">Loading "${name}"…</h1>`;
    document.getElementById("content").appendChild(pageDiv);
    
    addPinnedLink(pageId, `🎤`, name);
    navigateTo(pageId);
    
    try {
        const res = await fetch(`/api/artist/${encodeURIComponent(name)}`);
        const data = await res.json();
        
        let html = `
            <div class="detail-back" onclick="goBack()"><span>&larr;</span> Back</div>
            <div class="detail-header">
                ${data.image_url ? `<img src="${data.image_url}" class="detail-image artist-image" alt="${data.name}">` : ""}
                <div class="detail-name">${data.name}</div>
            </div>
        `;
        html += renderStatGrid(data.stats);
        
        html += `<div class="dashboard-grid">`;
        
        //Top Tracks
        html += `<div>
            <h2 class="section-title">Top Tracks</h2>
            <table class="data-table"><thead><tr><th>#</th><th>Title</th><th class="number-cell">Plays</th><th class="time-cell">Time</th></tr></thead><tbody>`;
        data.tracks.forEach((t, i) => {
            html += `<tr><td class="rank-cell ${rankClass(i)}">${i+1}</td><td class="name-cell">${t.title}</td><td class="number-cell">${t.play_count}</td><td class="time-cell">${t.listening_time}</td></tr>`;
        });
        if (data.tracks.length === 0) html += `<tr><td colspan="4" style="text-align: center; color: #a7a7a7;">No tracks found</td></tr>`;
        html += `</tbody></table>
            <button class="dashboard-more-btn" onclick="openPinnedSearch('${data.name.replace(/'/g, "\\'")}', 'tracks')">Show More</button>
        </div>`;
        
        //Top Albums
        html += `<div>
            <h2 class="section-title">Top Albums</h2>
            <table class="data-table"><thead><tr><th>#</th><th>Album</th><th class="number-cell">Plays</th><th class="time-cell">Time</th></tr></thead><tbody>`;
        data.albums.forEach((a, i) => {
            html += `<tr><td class="rank-cell ${rankClass(i)}">${i+1}</td><td class="name-cell clickable" onclick="openAlbumPage('${a.album.replace(/'/g, "\\'")}')">${a.album}</td><td class="number-cell">${a.play_count}</td><td class="time-cell">${a.listening_time}</td></tr>`;
        });
        if (data.albums.length === 0) html += `<tr><td colspan="4" style="text-align: center; color: #a7a7a7;">No albums found</td></tr>`;
        html += `</tbody></table>
            <button class="dashboard-more-btn" onclick="openPinnedSearch('${data.name.replace(/'/g, "\\'")}', 'albums')">Show More</button>
        </div>`;
        
        html += `</div>`; //Close dashboard-grid
        
        pageDiv.innerHTML = html;
    } catch (e) {
        pageDiv.innerHTML = `<h1 class="section-title">Error loading artist</h1>`;
        console.error("Artist page error:", e);
    }
}

//Open a pinned album detail page
async function openAlbumPage(name) {
    const pageId = `album-${slugify(name)}`;
    
    let pageDiv = document.getElementById(`page-${pageId}`);
    
    if (pageDiv) {
        navigateTo(pageId);
        return;
    }
    
    pageDiv = document.createElement("div");
    pageDiv.id = `page-${pageId}`;
    pageDiv.className = "page";
    pageDiv.innerHTML = `<h1 class="section-title">Loading "${name}"…</h1>`;
    document.getElementById("content").appendChild(pageDiv);
    
    addPinnedLink(pageId, `💿`, name);
    navigateTo(pageId);
    
    try {
        const res = await fetch(`/api/album/${encodeURIComponent(name)}`);
        const data = await res.json();
        
        let html = `
            <div class="detail-back" onclick="goBack()"><span>&larr;</span> Back</div>
            <div class="detail-header">
                ${data.image_url ? `<img src="${data.image_url}" class="detail-image album-image" alt="${data.name}">` : ""}
                <div>
                    <div class="detail-name">${data.name}</div>
                    ${data.artist ? `<div class="detail-subtitle">by ${makeArtistLinks(data.artist)}</div>` : ""}
                </div>
            </div>
        `;
        html += renderStatGrid(data.stats);
        
        html += `<table class="data-table"><thead><tr><th>#</th><th>Title</th><th>Artist</th><th class="number-cell">Plays</th><th class="time-cell">Listening Time</th></tr></thead><tbody>`;
        data.tracks.forEach((t, i) => {
            html += `<tr><td class="rank-cell ${rankClass(i)}">${i+1}</td><td class="name-cell">${t.title}</td><td class="artist-cell">${makeArtistLinks(t.artist)}</td><td class="number-cell">${t.play_count}</td><td class="time-cell">${t.listening_time}</td></tr>`;
        });
        if (data.tracks.length === 0) html += `<tr><td colspan="5" style="text-align: center; color: #a7a7a7;">No tracks found</td></tr>`;
        html += `</tbody></table>`;
        
        pageDiv.innerHTML = html;
    } catch (e) {
        pageDiv.innerHTML = `<h1 class="section-title">Error loading album</h1>`;
        console.error("Album page error:", e);
    }
}

//Add a pinned item to sidebar
function addPinnedLink(pageId, icon, label) {
    const pinnedContainer = document.getElementById("pinnedSearches");

    if (pinnedContainer.querySelector(`[data-page="${pageId}"]`)) {
        return; 
    }

    if (pinnedContainer.querySelectorAll(".pinned-link").length === 0) {
        pinnedContainer.innerHTML = `<div class="pinned-divider"></div><div class="pinned-header" style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0px;"><button class="pinned-close-all" onclick="closeAllPinned()">Close all</button></div>`;
    }
    
    const pinnedLink = document.createElement("a");
    pinnedLink.href = "#";
    pinnedLink.className = "nav-link pinned-link";
    pinnedLink.dataset.page = pageId;
    pinnedLink.innerHTML = `<span class="nav-icon">${icon}</span><span class="pinned-label">${label}</span><span class="pinned-close" data-pinned="${pageId}" title="Close">×</span>`;
    pinnedLink.addEventListener("click", (e) => {
        e.preventDefault();
        if (!e.target.classList.contains("pinned-close")) {
            navigateTo(pageId);
        }
    });
    pinnedLink.querySelector(".pinned-close").addEventListener("click", (e) => {
        e.stopPropagation();
        closePinnedPage(pageId);
    });
    pinnedContainer.appendChild(pinnedLink);
}

function goBack() {
    const pageToClose = currentPage;
    const pageToOpen = previousPage;

    if (document.getElementById(`page-${pageToOpen}`)) {
        navigateTo(pageToOpen);
    } else {
        navigateTo("dashboard");
    }
    
    if (pageToClose.startsWith("artist-") || pageToClose.startsWith("album-") || pageToClose.startsWith("pinned-")) {
        closePinnedPage(pageToClose);
    }
}

function navigateTo(page) {
    if (page !== currentPage) {
        previousPage = currentPage;
        currentPage = page;
    }
    
    //Update nav links
    document.querySelectorAll(".nav-link").forEach(link => {
        link.classList.toggle("active", link.dataset.page === page);
    });

    //Show/hide pages
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    const target = document.getElementById(`page-${page}`);
    if (target) target.classList.add("active");
    
    //Hide topBar on import page
    const topBar = document.getElementById("topBar");
    if (topBar) {
        topBar.style.display = (page === "import" ? "none" : "flex");
    }

    //Auto-focus search input when navigating to search page
    if (page === "search") {
        const landing = document.getElementById("search-landing");
        if (landing && landing.style.display !== "none") {
            setTimeout(() => document.getElementById("searchInputLanding").focus(), 50);
        }
    }
    
    //Smooth scroll to top
    window.scrollTo(0, 0);

    if (page === "import") {
        renderImportPage();
    }
}

async function renderImportPage() {
    const listContainer = document.getElementById("db-list");
    if (!listContainer) return;

    try {
        const [dbs, current] = await Promise.all([
            fetch('/api/databases').then(res => res.json()),
            fetch('/api/databases/current').then(res => res.json())
        ]);

        if (dbs.length === 0) {
            listContainer.innerHTML = `<div class="no-data">No databases found in backend folder.</div>`;
            return;
        }

        listContainer.innerHTML = dbs.map(db => {
            const isActive = db.name === current.current;
            const sizeMB = (db.size / (1024 * 1024)).toFixed(1);

            return `
                <div class="db-card ${isActive ? 'active' : ''}" 
                     onclick="${!isActive ? `switchDatabase('${db.name}')` : ''}"
                     style="${isActive ? 'cursor: default;' : 'cursor: pointer;'}">
                    <div class="db-card-info">
                        <div class="db-name" style="font-weight: bold; font-size: 1.1rem; margin-bottom: 4px;">${db.name}</div>
                        <div class="db-meta" style="font-size: 0.85rem; color: var(--text-muted);">
                            ${sizeMB} MB • Modifié le ${db.modified}
                        </div>
                    </div>
                    <div class="db-card-action">
                        <button class="db-append-btn" id="append-btn-${db.name.replace(/[^a-z0-9]/gi, '_')}" onclick="triggerAppend('${db.name}'); event.stopPropagation();" title="Add files to this database">
                            +
                        </button>
                        <button class="db-select-btn ${isActive ? 'active' : ''}" ${isActive ? 'disabled' : ''}>
                            ${isActive ? 'Selected' : 'Select'}
                        </button>
                        ${!isActive ? `
                            <button class="db-delete-btn" onclick="deleteDatabase('${db.name}'); event.stopPropagation();" title="Delete Database">
                                🗑️
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join("");

        initImportDropZone();

    } catch (e) {
        listContainer.innerHTML = `<div class="no-data" style="color: var(--danger);">Error loading databases: ${e.message}</div>`;
    }
}

let stagedFilesMap = new Map(); //Key: name-size, Value: File object

function initImportDropZone() {
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const folderInput = document.getElementById("folder-input");
    const browseFiles = document.getElementById("browse-files");
    const browseFolder = document.getElementById("browse-folder");
    const createBtn = document.getElementById("create-db-btn");
    
    if (!dropZone || !fileInput || !folderInput) return;

    //Click handlers
    if (browseFiles) browseFiles.onclick = (e) => { e.stopPropagation(); fileInput.click(); };
    if (browseFolder) browseFolder.onclick = (e) => { e.stopPropagation(); folderInput.click(); };
    dropZone.onclick = (e) => { if (e.target !== browseFiles && e.target !== browseFolder) fileInput.click(); };

    fileInput.onchange = () => { handleFiles(fileInput.files); fileInput.value = ""; };
    folderInput.onchange = () => { handleFiles(folderInput.files); folderInput.value = ""; };

    //Drag & Drop
    dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add("dragover"); };
    dropZone.ondragleave = () => dropZone.classList.remove("dragover");
    dropZone.ondrop = (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        const items = e.dataTransfer.items;
        if (items) {
            for (let i = 0; i < items.length; i++) {
                const item = items[i].webkitGetAsEntry();
                if (item) traverseFileTree(item);
            }
        } else {
            handleFiles(e.dataTransfer.files);
        }
    };

    if (createBtn) {
        createBtn.onclick = async () => {
            const nameInput = document.getElementById("new-db-name");
            const name = nameInput.value.trim() || `DataBase ${Date.now()}`;
            
            if (stagedFilesMap.size === 0) {
                alert("Please add some files first.");
                return;
            }

            //UI: Loading state
            const originalText = createBtn.innerText;
            createBtn.disabled = true;
            createBtn.innerText = "Creating & Importing... (this may take a few minutes)";
            createBtn.style.opacity = "0.7";

            try {
                const formData = new FormData();
                formData.append("name", name);
                stagedFilesMap.forEach((file) => formData.append("files", file));

                const response = await fetch('/api/databases/create', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.error) {
                    alert(`Error: ${data.error}`);
                    return;
                }

                // Poll for progress
                const taskId = data.task_id;
                const pollInterval = setInterval(async () => {
                    try {
                        const statusRes = await fetch(`/api/import/status/${taskId}`);
                        const status = await statusRes.json();

                        if (status.progress) {
                            if (status.progress.startsWith("DONE:")) {
                                clearInterval(pollInterval);
                                createBtn.disabled = false;
                                createBtn.innerText = originalText;
                                createBtn.style.opacity = "1";
                                const dbName = status.progress.replace("DONE:", "");
                                alert(`Database "${dbName}" created and imported successfully!`);
                                stagedFilesMap.clear();
                                nameInput.value = "";
                                renderStagedFiles();
                                await renderImportPage();
                                location.reload();
                            } else if (status.progress.startsWith("ERROR:")) {
                                clearInterval(pollInterval);
                                createBtn.disabled = false;
                                createBtn.innerText = originalText;
                                createBtn.style.opacity = "1";
                                alert(`Error: ${status.progress.replace("ERROR:", "")}`);
                            } else {
                                createBtn.innerText = status.progress;
                            }
                        }

                        if (status.status === "done" || status.status === "error") {
                            clearInterval(pollInterval);
                            createBtn.disabled = false;
                            createBtn.innerText = originalText;
                            createBtn.style.opacity = "1";
                        }
                    } catch (e) {
                        console.error("Poll error:", e);
                    }
                }, 1000);

            } catch (e) {
                console.error("Upload Error:", e);
                alert(`Upload failed: ${e.message}`);
                createBtn.disabled = false;
                createBtn.innerText = originalText;
                createBtn.style.opacity = "1";
            }
        };
    }

    renderStagedFiles();
}

function traverseFileTree(item, path = "") {
    if (item.isFile) {
        item.file((file) => handleFiles([file]));
    } else if (item.isDirectory) {
        const dirReader = item.createReader();
        const readBatch = () => {
            dirReader.readEntries((entries) => {
                if (entries.length > 0) {
                    for (const entry of entries) traverseFileTree(entry, path + item.name + "/");
                    readBatch();
                }
            });
        };
        readBatch();
    }
}

async function processZip(file) {
    try {
        const zip = await JSZip.loadAsync(file);
        const extracted = [];
        for (const [filename, zipEntry] of Object.entries(zip.files)) {
            if (zipEntry.dir) continue;
            const nameOnly = filename.split('/').pop();
            if (!nameOnly.startsWith("._") && nameOnly.toLowerCase().endsWith(".json") && nameOnly.includes("Streaming_History_Audio")) {
                const blob = await zipEntry.async("blob");
                extracted.push(new File([blob], nameOnly, { type: "application/json" }));
            }
        }
        if (extracted.length > 0) handleFiles(extracted);
    } catch (e) {
        console.error("ZIP Error:", e);
    }
}

function handleFiles(files) {
    let changed = false;
    for (const f of files) {
        if (f.name.toLowerCase().endsWith(".zip")) {
            processZip(f);
            continue;
        }

        const name = f.name;
        const isJson = name.toLowerCase().endsWith(".json");
        const isAudio = name.includes("Streaming_History_Audio");
        const isXlsx = name.toLowerCase().endsWith(".xlsx");

        //Filter: Only .json files (Spotify) OR .xlsx files (Deezer)
        //CRITICAL: Filter out macOS metadata files starting with ._
        if (name.startsWith("._")) continue;
        if (!isXlsx && (!isJson || !isAudio)) continue;
        
        const key = `${name}-${f.size}`;
        if (!stagedFilesMap.has(key)) {
            stagedFilesMap.set(key, f);
            changed = true;
        }
    }
    if (changed) renderStagedFiles();
}

function removeStagedFile(key) {
    if (stagedFilesMap.delete(key)) {
        renderStagedFiles();
    }
}

function renderStagedFiles() {
    const list = document.getElementById("staged-files");
    const area = document.getElementById("create-db-area");
    if (!list || !area) return;

    if (stagedFilesMap.size === 0) {
        list.innerHTML = "";
        area.style.display = "none";
        return;
    }

    area.style.display = "block";
    let html = "";
    stagedFilesMap.forEach((f, key) => {
        html += `
            <div class="staged-file-item">
                <span>📄 ${f.name} (${(f.size / 1024).toFixed(1)} KB)</span>
                <span class="staged-file-remove" onclick="removeStagedFile('${key}')">✕</span>
            </div>
        `;
    });
    list.innerHTML = html;

    const nameInput = document.getElementById("new-db-name");
    if (nameInput && !nameInput.value) setNextDefaultDbName();
}

async function setNextDefaultDbName() {
    try {
        const dbs = await fetch('/api/databases').then(res => res.json());
        const existingNames = dbs.map(db => db.name.toLowerCase());
        
        let i = 1;
        while (existingNames.includes(`database ${i}.db`)) {
            i++;
        }
        const nameInput = document.getElementById("new-db-name");
        if (nameInput) nameInput.value = `DataBase ${i}`;
    } catch (e) {
        console.error("Error setting default DB name:", e);
    }
}

async function switchDatabase(name) {
    if (!confirm(`Switch to database "${name}"?`)) return;

    try {
        const res = await fetch('/api/databases/select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();
        
        if (data.success) {
            alert(`Switched to ${name}`);
            window.location.reload(); 
        } else {
            alert(`Error: ${data.error || 'Unknown error'}`);
        }
    } catch (e) {
        console.error(e);
        alert(`Error: ${e.message}`);
    }
}

async function deleteDatabase(name) {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) return;

    try {
        const res = await fetch(`/api/databases/${name}`, {
            method: 'DELETE'
        });
        
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();
        
        if (data.success) {
            alert(`Database "${name}" deleted.`);
            renderImportPage();
        } else {
            alert(`Error: ${data.error || 'Unknown error'}`);
        }
    } catch (e) {
        console.error(e);
        alert(`Error: ${e.message}`);
    }
}

function triggerAppend(dbName) {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '.json,.xlsx,.zip';
    
    input.onchange = (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            appendDatabase(dbName, files);
        }
    };
    
    input.click();
}

async function appendDatabase(dbName, files) {
    const btnId = `append-btn-${dbName.replace(/[^a-z0-9]/gi, '_')}`;
    const btn = document.getElementById(btnId);
    const originalText = btn ? btn.innerText : '+';

    if (btn) {
        btn.disabled = true;
        btn.style.width = "auto";
        btn.style.padding = "0 10px";
    }

    try {
        const formData = new FormData();
        formData.append("name", dbName);
        files.forEach(f => formData.append("files", f));

        const response = await fetch('/api/databases/append', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        // Poll for progress
        const taskId = data.task_id;
        const pollInterval = setInterval(async () => {
            try {
                const statusRes = await fetch(`/api/import/status/${taskId}`);
                const status = await statusRes.json();

                if (status.progress) {
                    if (status.progress.startsWith("DONE:")) {
                        clearInterval(pollInterval);
                        if (btn) { btn.disabled = false; btn.innerText = originalText; btn.style.width = ""; btn.style.padding = ""; }
                        alert(`Files successfully added to "${dbName}"!`);
                        renderImportPage();
                        if (document.querySelector(`.db-card.active .db-name`)?.innerText === dbName) {
                            location.reload();
                        }
                    } else if (status.progress.startsWith("ERROR:")) {
                        clearInterval(pollInterval);
                        if (btn) { btn.disabled = false; btn.innerText = originalText; btn.style.width = ""; btn.style.padding = ""; }
                        alert(`Error: ${status.progress.replace("ERROR:", "")}`);
                    } else if (btn) {
                        btn.innerText = status.progress;
                    }
                }

                if (status.status === "done" || status.status === "error") {
                    clearInterval(pollInterval);
                    if (btn) { btn.disabled = false; btn.innerText = originalText; btn.style.width = ""; btn.style.padding = ""; }
                }
            } catch (e) {
                console.error("Poll error:", e);
            }
        }, 1000);

    } catch (e) {
        console.error("Append Error:", e);
        alert(`Append failed: ${e.message}`);
        if (btn) { btn.disabled = false; btn.innerText = originalText; btn.style.width = ""; btn.style.padding = ""; }
    }
}

// Initial binding
document.querySelectorAll(".nav-link:not(.pinned-link)").forEach(link => {
    link.addEventListener("click", (e) => {
        e.preventDefault();
        navigateTo(link.dataset.page);
    });
});

async function fetchGeneralStats(start_date="", end_date=""){
    try {
        const response = await fetch(`/api/stats/general?start_date=${start_date}&end_date=${end_date}`);
        const data = await response.json();
        
        document.getElementById("listening-time").textContent = data.listening_time;
        document.getElementById("total-streams").textContent = data.total_plays;
        
        document.getElementById("unique-artists").textContent = data.total_artists.toLocaleString();
        document.getElementById("unique-tracks").textContent = data.total_tracks.toLocaleString();
        document.getElementById("unique-albums").textContent = data.total_albums.toLocaleString();
        
    } catch (error) {
        console.error("Error:", error);    
    }
}

async function fetchTopTracks(limit=5, param=1, start_date="", end_date=""){
    try {
        const response = await fetch(`/api/top/tracks?limit=${limit}&param=${param}&start_date=${start_date}&end_date=${end_date}`);
        const tracks = await response.json();
        
        const listDash = document.getElementById("dash-tracks-list");
        const listPage = document.getElementById("page-tracks-list");
        
        listDash.innerHTML = "";
        if (listPage) listPage.innerHTML = "";
        
        tracks.forEach((track, index) => {
            const trStr = `
                <td class="rank-cell ${rankClass(index)}">${index + 1}</td>
                <td class="name-cell">${track.title}</td>
                <td class="artist-cell">${makeArtistLinks(track.artist)}</td>
                <td class="number-cell">${track.play_count}</td>
                <td class="time-cell">${track.listening_time}</td>
            `;
            
            // Limit dashboard to 10 max
            if (index < 10) {
                const trDash = document.createElement("tr");
                trDash.innerHTML = trStr;
                listDash.appendChild(trDash);
            }
            
            if (listPage) {
                const trPage = document.createElement("tr");
                trPage.innerHTML = trStr;
                listPage.appendChild(trPage);
            }
        });
        
    } catch (error) {
        console.error("Error: ", error);
    }
}


async function fetchTopArtists(limit=5, param=1, start_date="", end_date=""){
    try {
        const response = await fetch(`/api/top/artists?limit=${limit}&param=${param}&start_date=${start_date}&end_date=${end_date}`);
        const artists = await response.json();
        
        const listDash = document.getElementById("dash-artists-list");
        const listPage = document.getElementById("page-artists-list");
        
        listDash.innerHTML = "";
        if (listPage) listPage.innerHTML = "";
        
        artists.forEach((artist, index) => {
            const trStr = `
                <td class="rank-cell ${rankClass(index)}">${index + 1}</td>
                <td class="name-cell clickable" onclick="openArtistPage('${artist.name.replace(/'/g, "\\'")}')"> ${artist.name}</td>
                <td class="number-cell">${artist.play_count}</td>
                <td class="time-cell">${artist.listening_time}</td>
            `;
            
            if (index < 10) {
                const trDash = document.createElement("tr");
                trDash.innerHTML = trStr;
                listDash.appendChild(trDash);
            }
            
            if (listPage) {
                const trPage = document.createElement("tr");
                trPage.innerHTML = trStr;
                listPage.appendChild(trPage);
            }
        });
        
    } catch (error) {
        console.error("Error: ", error);
    }
}

async function fetchTopAlbums(limit=5, param=1, start_date="", end_date=""){
    try {
        const response = await fetch(`/api/top/albums?limit=${limit}&param=${param}&start_date=${start_date}&end_date=${end_date}`);
        const albums = await response.json();
        
        const listPage = document.getElementById("page-albums-list");
        if (listPage) listPage.innerHTML = "";
        
        albums.forEach((album, index) => {
            const trStr = `
                <td class="rank-cell ${rankClass(index)}">${index + 1}</td>
                <td class="name-cell clickable" onclick="openAlbumPage('${album.album.replace(/'/g, "\\'")}')"> ${album.album}</td>
                <td class="artist-cell">${makeArtistLinks(album.artist)}</td>
                <td class="number-cell">${album.play_count}</td>
                <td class="time-cell">${album.listening_time}</td>
            `;
            
            if (listPage) {
                const trPage = document.createElement("tr");
                trPage.innerHTML = trStr;
                listPage.appendChild(trPage);
            }
        });
        
    } catch (error) {
        console.error("Error: ", error);
    }
}

let limits = { tracks: 25, artists: 25, albums: 25 };
let currentStartDate = "";
let currentEndDate = "";
let currentSortMode = "0";

function applyFilters(start, end) {
    currentStartDate = start;
    currentEndDate = end;
    
    fetchGeneralStats(start, end);
    fetchTopTracks(limits.tracks, currentSortMode, start, end);
    fetchTopArtists(limits.artists, currentSortMode, start, end);
    fetchTopAlbums(limits.albums, currentSortMode, start, end);
}

// Sort button logic
document.querySelectorAll(".sort-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".sort-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        
        currentSortMode = btn.dataset.sort;
        applyFilters(currentStartDate, currentEndDate);
    });
});

// Preset filter logic
document.querySelectorAll(".filter-btn:not(.sort-btn)").forEach(btn => {
    btn.addEventListener("click", () => {
        // Update active class only for period buttons (not sort buttons)
        document.querySelectorAll(".filter-btn:not(.sort-btn)").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        
        const filterStr = btn.dataset.filter;
        const customContainer = document.getElementById("filterCustom");
        
        if (filterStr === "custom") {
            customContainer.style.display = "flex";
            return;
        } else {
            customContainer.style.display = "none";
        }
        
        let start = "", end = "";
        const year = new Date().getFullYear();
        
        if (filterStr === "this_year") {
            start = `${year}-01-01`;
            end = `${year}-12-31`;
        } else if (filterStr === "last_year") {
            start = `${year - 1}-01-01`;
            end = `${year - 1}-12-31`;
        } // "all" stays "" and ""
        
        applyFilters(start, end);
    });
});

// Initial load: All Time
applyFilters("", "");

// Custom Apply button
document.getElementById("apply-btn").addEventListener("click", () => {
    const startDate = document.getElementById("start-date").value;
    const endDate = document.getElementById("end-date").value;
    applyFilters(startDate, endDate);
});

// See more buttons
document.getElementById("more-tracks-btn").addEventListener("click", () => {
    limits.tracks += 25; // Add more items
    const param = currentSortMode;
    const sd = document.getElementById("start-date").value;
    const ed = document.getElementById("end-date").value;
    fetchTopTracks(limits.tracks, param, sd, ed);
});

document.getElementById("more-artists-btn").addEventListener("click", () => {
    limits.artists += 25;
    const param = currentSortMode;
    const sd = document.getElementById("start-date").value;
    const ed = document.getElementById("end-date").value;
    fetchTopArtists(limits.artists, param, sd, ed);
});

document.getElementById("more-albums-btn").addEventListener("click", () => {
    limits.albums += 25;
    const param = document.getElementById("sort-param") ? document.getElementById("sort-param").value : currentSortMode;
    const sd = document.getElementById("start-date").value;
    const ed = document.getElementById("end-date").value;
    fetchTopAlbums(limits.albums, param, sd, ed);
});

// Search logic
let currentSearchQuery = "";

function performSearch(q) {
    if (!q) return;
    
    currentSearchQuery = q;
    
    // Switch from landing to results
    document.getElementById("search-landing").style.display = "none";
    document.getElementById("search-results").style.display = "block";
    
    // Sync both inputs
    document.getElementById("searchInput").value = q;
    document.getElementById("searchInputLanding").value = q;
    
    navigateTo("search");
    
    fetch(`/api/search?q=${encodeURIComponent(q)}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById("search-title").textContent = `Search Results for "${q}"`;
            document.getElementById("search-nav-artists").textContent = `Artists (${data.artists.length})`;
            document.getElementById("search-nav-tracks").textContent = `Tracks (${data.tracks.length})`;
            document.getElementById("search-nav-albums").textContent = `Albums (${data.albums.length})`;
            
            const listA = document.getElementById("search-artists-list");
            listA.innerHTML = "";
            data.artists.forEach((a) => {
                listA.innerHTML += `<tr>
                    <td class="name-cell clickable" onclick="openArtistPage('${a.name.replace(/'/g, "\\'")}')">${a.name}</td>
                    <td class="number-cell">${a.play_count}</td>
                    <td class="time-cell">${a.listening_time}</td>
                </tr>`;
            });
            if (data.artists.length === 0) listA.innerHTML = `<tr><td colspan="3" style="text-align: center; color: #a7a7a7;">No artists found</td></tr>`;
            
            const listT = document.getElementById("search-tracks-list");
            listT.innerHTML = "";
            data.tracks.forEach((t) => {
                listT.innerHTML += `<tr>
                    <td class="name-cell">${t.name}</td>
                    <td class="artist-cell">${makeArtistLinks(t.artist)}</td>
                    <td class="number-cell">${t.play_count}</td>
                    <td class="time-cell">${t.listening_time}</td>
                </tr>`;
            });
            if (data.tracks.length === 0) listT.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #a7a7a7;">No tracks found</td></tr>`;
            
            const listAl = document.getElementById("search-albums-list");
            listAl.innerHTML = "";
            data.albums.forEach((ab) => {
                listAl.innerHTML += `<tr>
                    <td class="name-cell clickable" onclick="openAlbumPage('${ab.name.replace(/'/g, "\\'")}')">${ab.name}</td>
                    <td class="artist-cell">${makeArtistLinks(ab.artist)}</td>
                    <td class="number-cell">${ab.play_count}</td>
                    <td class="time-cell">${ab.listening_time}</td>
                </tr>`;
            });
            if (data.albums.length === 0) listAl.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #a7a7a7;">No albums found</td></tr>`;
        })
        .catch(e => console.error("Search error: ", e));
}

// Top bar search
document.getElementById("searchBtn").addEventListener("click", () => {
    performSearch(document.getElementById("searchInput").value.trim());
});
document.getElementById("searchInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") document.getElementById("searchBtn").click();
});

// Landing page search
document.getElementById("searchBtnLanding").addEventListener("click", () => {
    performSearch(document.getElementById("searchInputLanding").value.trim());
});
document.getElementById("searchInputLanding").addEventListener("keypress", (e) => {
    if (e.key === "Enter") document.getElementById("searchBtnLanding").click();
});
    

// Show More buttons → open pinned search detail page
document.getElementById("search-more-artists").addEventListener("click", () => openPinnedSearch(currentSearchQuery, "artists"));
document.getElementById("search-more-tracks").addEventListener("click", () => openPinnedSearch(currentSearchQuery, "tracks"));
document.getElementById("search-more-albums").addEventListener("click", () => openPinnedSearch(currentSearchQuery, "albums"));

// Pinned search pages
let pinnedCounter = 0;

async function openPinnedSearch(query, type) {
    if (!query) return;
    
    pinnedCounter++;
    const pageId = `pinned-${pinnedCounter}`;
    const typeLabel = type.charAt(0).toUpperCase() + type.slice(1);
    
    // Create page div in main content
    const pageDiv = document.createElement("div");
    pageDiv.id = `page-${pageId}`;
    pageDiv.className = "page";
    document.getElementById("content").appendChild(pageDiv);
    
    // Add sidebar link using helper
    addPinnedLink(pageId, `🔍`, `${typeLabel}: "${query}"`);
    
    // Navigate to it
    navigateTo(pageId);
    
    // Fetch expanded results (limit=100)
    try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=100`);
        const data = await res.json();
        
        let tableHTML = "";
        if (type === "artists") {
            tableHTML = `<table class="data-table"><thead><tr><th>#</th><th>Artist</th><th class="number-cell">Plays</th><th class="time-cell">Listening Time</th></tr></thead><tbody>`;
            data.artists.forEach((a, i) => {
                tableHTML += `<tr><td class="rank-cell ${rankClass(i)}">${i+1}</td><td class="name-cell clickable" onclick="openArtistPage('${a.name.replace(/'/g, "\\'")}')">${a.name}</td><td class="number-cell">${a.play_count}</td><td class="time-cell">${a.listening_time}</td></tr>`;
            });
            tableHTML += `</tbody></table>`;
        } else if (type === "tracks") {
            tableHTML = `<table class="data-table"><thead><tr><th>#</th><th>Title</th><th>Artist</th><th class="number-cell">Plays</th><th class="time-cell">Listening Time</th></tr></thead><tbody>`;
            data.tracks.forEach((t, i) => {
                tableHTML += `<tr><td class="rank-cell ${rankClass(i)}">${i+1}</td><td class="name-cell">${t.name}</td><td class="artist-cell">${makeArtistLinks(t.artist)}</td><td class="number-cell">${t.play_count}</td><td class="time-cell">${t.listening_time}</td></tr>`;
            });
            tableHTML += `</tbody></table>`;
        } else if (type === "albums") {
            tableHTML = `<table class="data-table"><thead><tr><th>#</th><th>Album</th><th>Artist</th><th class="number-cell">Plays</th><th class="time-cell">Listening Time</th></tr></thead><tbody>`;
            data.albums.forEach((ab, i) => {
                tableHTML += `<tr><td class="rank-cell ${rankClass(i)}">${i+1}</td><td class="name-cell clickable" onclick="openAlbumPage('${ab.name.replace(/'/g, "\\'")}')">${ab.name}</td><td class="artist-cell">${makeArtistLinks(ab.artist)}</td><td class="number-cell">${ab.play_count}</td><td class="time-cell">${ab.listening_time}</td></tr>`;
            });
            tableHTML += `</tbody></table>`;
        }
        
        pageDiv.innerHTML = `<h1 class="section-title">${typeLabel} matching "${query}"</h1>${tableHTML}`;
    } catch (e) {
        pageDiv.innerHTML = `<h1 class="section-title">Error loading results</h1>`;
        console.error("Pinned search error:", e);
    }
}

function closePinnedPage(pageId) {
    // Remove page
    const page = document.getElementById(`page-${pageId}`);
    if (page) page.remove();
    
    // Remove sidebar link
    const pinnedContainer = document.getElementById("pinnedSearches");
    const link = pinnedContainer.querySelector(`[data-page="${pageId}"]`);
    if (link) link.remove();
    
    // If no more pinned, remove header
    if (pinnedContainer.querySelectorAll(".pinned-link").length === 0) {
        pinnedContainer.innerHTML = "";
    }
    
    // Navigate back to search if we were on this page
    if (currentPage === pageId) {
        navigateTo("search");
    }
}

function closeAllPinned() {
    const pinnedContainer = document.getElementById("pinnedSearches");
    pinnedContainer.querySelectorAll(".pinned-link").forEach(link => {
        const pageId = link.dataset.page;
        const page = document.getElementById(`page-${pageId}`);
        if (page) page.remove();
    });
    pinnedContainer.innerHTML = "";
    if (currentPage.startsWith("pinned-") || currentPage.startsWith("artist-") || currentPage.startsWith("album-")) {
        navigateTo("dashboard");
    }
}
