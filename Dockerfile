FROM debian AS container-metrics
    RUN apt-get update && \
        apt-get install -y \
        python3 \
        python3-pip

    WORKDIR /home/container-metrics

    COPY ./src /home/container-metrics/

    # create entrypoint
    RUN echo "#!/bin/bash">/home/entrypoint.sh
    RUN echo "python3 -u /home/container-metrics/container-metrics.py \"\$@\"">>/home/entrypoint.sh
    RUN echo "exit \$?">>/home/entrypoint.sh
    RUN chmod +x /home/entrypoint.sh

    ENTRYPOINT [ "/home/entrypoint.sh" ]
