FROM apache/superset:4.1.4

USER root
RUN pip install --no-cache-dir duckdb==1.4.5 duckdb-engine==0.17.0
COPY superset /opt/datalake/superset
COPY sql /opt/datalake/sql
USER superset

CMD ["sh", "/opt/datalake/superset/iniciar.sh"]
