# UKR
This code can be used in 2 configurations:
- calculatng indexes for historical data - manually add folders with satellite images to **data** folder
- calculating indexes for actual data - automatic download of satellite images (it can be searched by specififed extent, cloud cover and start / end date)
# Setup:
1) Clone the repository and add manually 5 folders named **data**, **reproject**, **results**, **share** and **structureArchive**
2) Go to **settings.py**, 
    - add your credentials, 
    - change start and end date for automatic data download (it works for actual data only), 
    - change oblast signature, 
    - choose if you want to calculate historical or actual indexes (uncomment proper indexes variable)
    - change acceptable cloud cover range (it works for actual data only)
3) Add simplified extent in .geojson file of your area of interest for satellite images search to **geojsonExtents** folder, name it with oblast signature
4) Add detailed extent of your are of interest to **oblastExtent** folder as SHP, name it with oblast signature
5) Create a proper Python environment, run the project by **python main.py**
