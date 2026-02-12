{% docs __overview__ %}
# Airflow + dbt con agentes en accion

Este proyecto prueba como funciona Airflow con dbt y un agente que lee la documentacion para entender el pipeline. Vamos a tener DAGS que pegan a APIs publicas, cargan la data en raw, y luego modelos que transforman hasta la capa silver.

**Lineas principales**
- Ingesta desde APIs publicas con DAGS dedicados.
- Modelos dbt que transforman de raw a silver.
- Consumo desde `source()` en la capa raw (no usamos seeds como fuente).

Si queres explorar, empeza por los modelos y segui el linaje desde raw hasta silver.
{% enddocs %}
