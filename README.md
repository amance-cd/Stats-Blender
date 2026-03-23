Stats Blender : A Streaming platforms statics analysis tool - by Amance Celier Dennery

Quick recap of the project :

This projects aims at allowing any user of music streaming platforms (Spotify, Deezer...) to get a deep analysis of their listening habits. With Stats Blender, users can get their listening stats on their top tracks, artists, and albums, sorted by number of plays or listening time. They can also choose on which time period they want their stats from. 
For instance Stats Blender can be useful for users at the end of the year, when streaming platforms release their yearly recap, not giving a lot of detail. With Stats Blender, users can get to see how much they've listened to any artist or song during the year, as well as for any time period. 
The name "Stats Blender" comes from the idea of blending users streaming histories from different platforms to get a complete overview of their all time listening habits.
For now it only works with Spotify and Deezer, but Apple Music compatibilty will be available soon.



Get started using Stats Blender :

In a terminal window enter :

git clone https://github.com/amance-cd/Stats-Blender.git

then if you're on MacOS :
cd Stats-Blender/v4 && ./start.sh

or if you're on Windows :
cd Stats-Blender/v4 && start.bat

(or cd Stats-Blender/v3 if you want to use the original interface) 

To discover using the app, a sample history is already loaded, allowing you to see how the app works without having to load your own history. You can use any feature with this sample history, browsing tracks, artists, and albums stats using the search tool, and selecting different time periods. 

Import your own history : 

To have access to your own listening history, you need to download it from the streaming platform you're using. The app uses Spotify API to get info on your history. To get acces to Spotify API, you need to create an app on https://developer.spotify.com/dashboard then click on your app and you will have access to your API keys. Copy them into .env.example and rename the file as .env.

For Spotify : Go to https://www.spotify.com/account/privacy/ with your account already logged in. Scroll down until you see the "Download your data" section. DO NOT SELECT "Account data" and "Technical log information", ONLY SELECT "Extended streaming history", then click on "Request data".
You will then receive an email to confirm your request, YOU HAVE TO CLICK ON THE LINK IN THE EMAIL TO CONFIRM YOUR REQUEST. 

For Deezer (assuming you're French): Aller sur https://www.deezer.com/account en étant connecté à son compte. Descendre un peu sur la page jusqu'à voir "Mes données personnelles" et cliquer dessus. Ensuite cliquer sur Demander mes données. Deezer vous enverra un code de sécurité par mail pour confirmer la demande, ce code peut prendre quelques minutes pour arriver. 

Both Spotify and Deezer data request take a few days to be processed, and you'll receive an email when your data is ready to be downloaded.

Importing data : 

If you only use Spotify, go to the import section on the app and select the "Spotify Extended Streaming History" folder you received. 
If you only use Deezer, go to the import section on the app and select the "deezer-data_XXXX.xlsx" file you received. 
If you use both, firstly import your Spotify data, and then import your Deezer data. 
As the app relies on Spotify API to ensure complete compatibility between platforms, Deezer history treatment can take a while. If your Spotify history is already loaded, the Deezer history treatment will be much faster, as some tracks from your Deezeer history will already be present in the Data Base. 




Upcoming features : 

I plan on adding Apple Music compatibility, as well as Deeze API integration, for quicker history treatment to users that only have Deezer.
I also plan on creating timed charts to display general stats, as well as charts for each artist/album. I will also add a song page to get further stats on each song. Finally, I want to integrate artist pictures/album covers on the general interface, to make it more visually appealing.




How it works : 

Importing data : When selecting your data files, the program will firstly analyze your history to get the data on every unique tracks played. It will then call Spotify API with spotipy to get additional data on each track. The data is then stored in a SQL database, with 5 tables for tracks, artists, albums, features and plays. 

If a Deezer history is loaded, the program will search for each track in the database to see if it already exists. If it does, only the play information is injected into the database. If it doesn't, it will call Spotify API with spotipy to get the track info.

Album cleaning : The program feature an album cleaning function to ensure that every version of a single album are merged together. Using Spotify API, the program can get the album type (album, compilation, single) and its tracklist length for each track. The purpose of this function is only keep real albums in one version only. For each track in the Spotify history, the program will check the album type corresponding. If the track is already present in the database with a different album, it will compare the new album type with the old one, using a score logic (album = 3, compilation = 2, single = 1). If both come from an album, the program keeps the longest one. This ensures that only one version of each album is kept, as the longest version contains every tracks. To further clean duplicate albums, another function is used to merge albums with the same beginning of name and same artist, but have words like "Deluxe", "Extended", "Special Edition" etc. 

Interface : After being injected into the database, the stats are displayed in a user-friendly interface, with a sidebar to navigate between the different pages, and a top bar to search for tracks, artists, or albums. Each click on the interface calls a specific app.js function, which retrieves the data from the database and displays it in the interface. When clicking on an artist/album page, a new page is created with the stats for that artist/album, and a API call is made to get the artist profile picture/album cover. 



Project Development : 

There are apps that already exists that provides the same statistical overview as Stats Blender,such as Stats.fm that I use since 2022. However, I always had some issues with these apps, firstly because I was a Deezer user before switching to Spotify and no app provided Deezer compatibility. The apps also had any issue on the way it was counting albums streams, some times having stats scattered accross different versions of the same album, resulting in having album stats not precise at all. Lastly, Stats.fm is a paid app, and I always loved being able to see what my friends and family were listening to, so I decided to make my own app, free to use, that was resolving these issues.   

V1 : I started working on this project during my first year of university, applying what I've learned in Python and Data Science courses. This part is available as V1 in the repository. The project relied on python dictionnaries to keep every stats, saved into pickle files to get access to the stats when I wanted. This part introduced me to Spotify API and was absolutely not optimized in any way, getting the stats from the API usually took several hours, and I oftenly had issue with Spotify API's rate limit, causing the development to be delayed by a whole day each time. V1 is simply a Jupyter file, very hard to read and understand, and not user-friendly at all. Still the core of the project was working, and I was able to see my listening stats from Spotify and Deezer combined in a simple text overlay. 

V2 : After learning more on coding I decided to rework the project from scratch to make it more efficient and easier to read even for me. I also decided to start working on an HTML interface to have an easier access to the stats. The interface was included into the Jupyter file, making it still difficult for non-coders to use. This part still relied on python dictionnaries and was not very optimized neither

V3 : I learned SQL in my second year of university, and decided to apply it to the project to make it more efficient. I also discovered spotipy, a python library that makes Spotify API requests much easier, and avoids getting 24 hours cooldown. The history treatment with API requests went from several hours to just a few minutes, even for my 100k+ streams history. I abandoned the Jupyter file and created mutliple python files to make the project more organized, and I started creating a web interface, using this time css and js in addition to html.

V4 : After creating the backend and the start of the frontend of V3, I decided to rework the user interface using generative AIs to make it more user-friendly and quicker to develop, as I have never took web development courses. This allowed me to add new features, keeping the structure and the seam files as V3, to keep the code organized and understandable for me to modify. I try to restrict my AI usage to small prompts, each time with a small feature to add, and I review every proposition before implementing it, to keep track of where the code is going and what it does. This allowed me add a research tool, create artist and album pages with profile pictures/album covers. I wanted a modern interface so I chose a black background, with purple accents. With this version, I consider the project finished, and I am proud to share it on internet for any user to enjoy for free. 






