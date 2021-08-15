import os
import time
import json
import logging
import requests
from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable

from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.latest_only_operator import LatestOnlyOperator
from airflow.exceptions import AirflowFailException

from comiccrawler.mission import Mission
from comiccrawler.analyzer import Analyzer, EpisodeList
from comiccrawler.episode import Episode


default_args = {
    'owner': 'Tsung Wu',
    'start_date': datetime(2021, 7, 21, 0, 0),
    'schedule_interval': '*/30 * * * *',
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    'max_active_runs': 1,
    'catchup': False
}

LINE_NOTIFY_API = 'https://notify-api.line.me/api/notify'


def process_metadata(mode, **context):
    file_dir = os.path.dirname(__file__)
    metadata_path = os.path.join(file_dir, '../data/comic.json')
    if mode == 'read':
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as fp:
                metadata = json.load(fp)
                print("Read History loaded: {}".format(metadata))
                return metadata
        else:
            return dict()

    elif mode == 'write':
        print("Saving latest comic information..")
        _, all_comic_info = context['task_instance'].xcom_pull(task_ids='check_comic_info')

        print(all_comic_info)
        # update to latest chapter
        with open(metadata_path, 'w') as fp:
            json.dump(all_comic_info, fp, indent=2, ensure_ascii=False)


def check_comic_info(**context):
    metadata = context['task_instance'].xcom_pull(task_ids='get_read_history')

    all_comic_info = dict(metadata)
    anything_new = dict()
    for comic_id in all_comic_info:
        comic_info = all_comic_info[comic_id]
        for comic in comic_info['source']:
            try:
                mission = Mission(url=comic['url'])
                Analyzer(mission).analyze()

                old_eps = EpisodeList([Episode(**e) for e in comic['episodes']])
                has_new_ep = False
                for ep in reversed(mission.episodes):
                    if old_eps.add(ep):
                        has_new_ep = True
                        ep_info = {
                            "comic_title": mission.title,
                            "chapter": ep.title,
                            "url": ep.url
                        }
                        if comic_id not in anything_new:
                            anything_new[comic_id] = [ep_info]
                        else:
                            anything_new[comic_id].append(ep_info)

                mission.episodes = [vars(ep) for ep in reversed(mission.episodes)]
                mission.module = None
                comic.update(vars(mission))

                if has_new_ep:
                    # download(mission, '/Volumes/photo/comic')
                    comic_info['last_update'] = time.time()
                    comic_info['last_update_datetime'] = str(datetime.now())
                    break
            except Exception as e:
                print(e)

    if len(anything_new) == 0:
        print("Nothing new now, prepare to end the workflow.")
    else:
        print(f"There are new chapter for {list(anything_new.keys())}")

    return anything_new, all_comic_info


def decide_what_to_do(**context):
    anything_new, all_comic_info = context['task_instance'].xcom_pull(task_ids='check_comic_info')

    print("Chekc init status")
    if len(anything_new) > 0:
        return 'yes_generate_notification'
    else:
        return 'no_do_nothing'


def send_line_notify(**context):
    anything_new, all_comic_info = context['task_instance'].xcom_pull(task_ids='check_comic_info')
    print(dict(anything_new))
    LINE_TOKEN = Variable.get('line_token_prod', None)
    if LINE_TOKEN is not None:

        for comic_id in dict(anything_new):
            for comic in anything_new[comic_id]:
                payload = {
                    'message': f"\n{comic_id} 更新拉！！！\n最新話: {comic['chapter']} \n{comic['url']}"
                }

                if all_comic_info[comic_id].get('thumbnail_url', None) is not None:
                    payload['imageThumbnail'] = all_comic_info[comic_id]['thumbnail_url']
                    payload['imageFullsize'] = all_comic_info[comic_id]['thumbnail_url']

                r = requests.post(LINE_NOTIFY_API, data=payload, headers={'Authorization': "Bearer " + LINE_TOKEN})

                if r.status_code != 200:
                    raise AirflowFailException('Send line notification fail: {}, msg: {}'.format(r.status_code, r.text))
    else:
        raise AirflowFailException('LINE Token not found')


with DAG('comic_update_pipeline', default_args=default_args, tags=['comictotal'], schedule_interval='*/30 * * * *') as dag:

    # define tasks
    latest_only = LatestOnlyOperator(task_id='latest_only')

    get_read_history = PythonOperator(
        task_id='get_read_history',
        python_callable=process_metadata,
        op_args=['read'],
        provide_context=True
    )

    check_comic_info = PythonOperator(
        task_id='check_comic_info',
        python_callable=check_comic_info,
        provide_context=True
    )

    decide_what_to_do = BranchPythonOperator(
        task_id='new_comic_available',
        python_callable=decide_what_to_do,
        provide_context=True
    )

    update_read_history = PythonOperator(
        task_id='update_read_history',
        python_callable=process_metadata,
        op_args=['write'],
        provide_context=True
    )

    send_notification = PythonOperator(
        task_id='yes_generate_notification',
        python_callable=send_line_notify,
        provide_context=True
    )

    do_nothing = DummyOperator(task_id='no_do_nothing')

    # define workflow
    latest_only >> get_read_history
    get_read_history >> check_comic_info
    check_comic_info >> update_read_history
    check_comic_info >> decide_what_to_do
    decide_what_to_do >> send_notification
    decide_what_to_do >> do_nothing
