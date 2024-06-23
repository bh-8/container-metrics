# **container-metrics**:
an extensible framework for feature extraction of container format files
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
- `docker compose build && ./container-metrics acquire mongodb://admin:admin@mongo-db:27017 collection io/mixed.blob --log=info`
- `docker compose build && ./container-metrics query mongodb://admin:admin@mongo-db:27017 collection yara --log=info`
- `docker compose build && ./container-metrics query mongodb://admin:admin@mongo-db:27017 collection json --log=info`
- `docker compose build && ./container-metrics query mongodb://admin:admin@mongo-db:27017 collection csv --log=info`
- `sudo rm -drf io/_csv/ io/_json/ io/_yara/ io/db/ && docker compose build && ./container-metrics acquire mongodb://admin:admin@mongo-db:27017 collection io/mixed3.blob --log=info && ./container-metrics query mongodb://admin:admin@mongo-db:27017 collection json --log=info`
## code conventions
- `general_identifier`
- `CamelCaseClassNames`
- `_private_variables`
