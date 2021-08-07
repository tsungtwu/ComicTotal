FROM apache/airflow:2.1.2
USER root
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash - \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
         nodejs \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*



USER airflow
ENV PYTHONPATH "${PYTHONPATH}:${AIRFLOW_HOME}"
COPY ./ComicCrawler ${AIRFLOW_HOME}/ComicCrawler
RUN cd ${AIRFLOW_HOME}/ComicCrawler \
  && pip install .