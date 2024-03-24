# container-metrics
B.Sc. thesis project
## getting started
### requirements
- docker engine (https://docs.docker.com/engine/)
- build plugin (https://docs.docker.com/build/)
- compose plugin (https://docs.docker.com/compose/)
### installation/build
- run `docker compose build` to download and build all required images
### usage
- start database services: `docker compose up --detach`
- basic usage/help: `./container-metrics`
- shutdown database services: `docker compose down`
### debugging
- `./container-metrics scan mongodb://admin:admin@mongo-db:27017 io/input/ --log debug`
## references
- Multimedia Authentication Testing: https://forensicworkinggroup.com/MAT.pdf
