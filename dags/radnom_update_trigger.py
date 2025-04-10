from airflow import DAG
from airflow.operators.latest_only import LatestOnlyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.exceptions import AirflowFailException


import time
from datetime import datetime, timedelta
import random
import pytz


def schedule_update_pipline():
    random.seed(time.time())
    now = datetime.now().astimezone(pytz.timezone('Asia/Taipei'))
    execution_date = now + timedelta(minutes=random.randint(20, 30))
    trigged_dag = trigger_dag(
        dag_id='comic_update_pipeline',
        conf={},
        execution_date=execution_date)

    if trigger_dag is not None:
        print(f'trigger update pipeline success, schedule on: {str(execution_date)}')
    else:
        print('trigger update pipeline fail')
        raise AirflowFailException('trigger update pipeline fail')


with DAG(
    dag_id="radnom_update_trigger",
    default_args={"owner": "tsungtwu"},
    start_date=days_ago(2),
    schedule_interval="*/40 16-17,23,0,3-15 * * *",
    tags=['comictotal'],
    catchup=False
) as dag:
    latest_only = LatestOnlyOperator(task_id='latest_only')

    trigger_operator = PythonOperator(
        task_id='trigger_update',
        python_callable=schedule_update_pipline
    )

    latest_only >> trigger_operator
