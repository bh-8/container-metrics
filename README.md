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
- `docker compose build && ./container-metrics acquire mongodb://admin:admin@mongo-db:27017 collection io/mixed.blob --log=debug`
- `docker compose build && ./container-metrics query mongodb://admin:admin@mongo-db:27017 collection yara --log=debug`
## references
- Multimedia Authentication Testing: https://forensicworkinggroup.com/MAT.pdf
- https://enfsi.eu/wp-content/uploads/2022/12/1.-BPM_Image-Authentication_ENFSI-BPM-DI-03-1.pdf
## code conventions
- `general_identifier`
- `CamelCaseClassNames`
- `_private_variables`
