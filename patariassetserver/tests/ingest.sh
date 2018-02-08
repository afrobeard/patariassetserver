# To ingest an image against an external identifier
curl --data-binary "@/Users/afrobeard/Scratch/whitehorse.jpg" "http://localhost:8080/assets/ingest/?external_identifier=banana"

# To get JSON of asset
wget http://localhost:8080/assets/a06e2d3d-1ae6-44cf-8f25-954c63caf833.json

# To get the default derivative image
wget http://localhost:8080/assets/a06e2d3d-1ae6-44cf-8f25-954c63caf833/

# To get the derivative
wget http://localhost:8080/assets/a06e2d3d-1ae6-44cf-8f25-954c63caf833/small/
wget http://localhost:8080/assets/a06e2d3d-1ae6-44cf-8f25-954c63caf833/medium/
wget http://localhost:8080/assets/a06e2d3d-1ae6-44cf-8f25-954c63caf833/large/

