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
from airflow.exceptions import AirflowFailException

from comiccrawler.mission import Mission
from comiccrawler.analyzer import Analyzer, EpisodeList
from comiccrawler.episode import Episode


default_args = {
    'owner': 'Tsung Wu',
    'start_date': datetime(2021, 7, 21, 0, 0),
    'schedule_interval': None,
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
        _, all_comic_info = context['task_instance'].xcom_pull(task_ids='init_comic_info')

        print(all_comic_info)

        # update to latest chapter
        with open(metadata_path, 'w') as fp:
            json.dump(all_comic_info, fp, indent=2, ensure_ascii=False)


def parse_new_comic(**context):
    arg = get_parameters(context=context)
    url = arg.get('url')
    thumbnail_url = arg.get('thumbnail_url', None)

    if url is not None:
        return url, thumbnail_url
    else:
        raise AirflowFailException('request parse failed')


def init_comic_info(**context):

    metadata = context['task_instance'].xcom_pull(task_ids='get_read_history')
    url, thumbnail_url = context['task_instance'].xcom_pull(task_ids='parse_new_comic')
    all_comic_info = dict(metadata)
    comic_id = None
    comic_info = {
        "name": None,
        "last_update": None,
        "last_update_datetime": None,
        "latest_chapter": None,
        "thumbnail_url": thumbnail_url,
        "source": [
            {
                "title": None,
                "url": url,
                "episodes": []

            }
        ]
    }
    anything_new = dict()
    for comic in comic_info['source']:
        mission = Mission(url=comic['url'])
        Analyzer(mission).analyze()
        comic_info['name'] = mission.title
        comic_id = mission.title
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
                    anything_new[comic_id] = {"url": comic['url'], "episodes": [ep_info]}
                else:
                    anything_new[comic_id]['episodes'].append(ep_info)

        mission.episodes = [vars(e) for e in old_eps]
        mission.module = None
        comic.update(vars(mission))

        comic_info['last_update'] = time.time()
        comic_info['last_update_datetime'] = str(datetime.now())

    print(f"Update Comic {comic_id}")
    all_comic_info[comic_id] = comic_info

    return anything_new, all_comic_info


def decide_what_to_do(**context):
    anything_new, all_comic_info = context['task_instance'].xcom_pull(task_ids='init_comic_info')

    print("Chekc init status")
    if len(anything_new) > 0:
        return 'yes_generate_notification'
    else:
        return 'no_do_nothing'


def send_line_notify(**context):
    anything_new, all_comic_info = context['task_instance'].xcom_pull(task_ids='init_comic_info')
    print(f'new comic: {anything_new}')

    CHANNEL_ACCESS_TOKEN = Variable.get('LINE_CHANNEL_ACCESS_TOKEN', None)

    if CHANNEL_ACCESS_TOKEN is not None:
        LINE_MESSAGING_API = "https://api.line.me/v2/bot/message/push"
        GROUP_ID = Variable.get('LINE_GROUP_ID', None)  # 群組的 ID

        if GROUP_ID is None:
            raise AirflowFailException('LINE Group ID not found')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
        }

        # 使用GitHub上的圖片URL
        cat_meme_url = "https://raw.githubusercontent.com/tsungtwu/ComicTotal/refs/heads/master/data/new_comic_cat_meme.jpg"

        for comic_id in dict(anything_new):
            print(f'send notification: {comic_id}')

            # 創建Flex Message
            flex_message = {
                "type": "flex",
                "altText": f"奇怪的漫畫增加了: {comic_id}",
                "contents": {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": cat_meme_url,
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "cover"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "奇怪的漫畫增加了",
                                "weight": "bold",
                                "size": "xl",
                                "color": "#ff5551"
                            },
                            {
                                "type": "text",
                                "text": comic_id,
                                "weight": "bold",
                                "size": "lg",
                                "margin": "md"
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "action": {
                                    "type": "uri",
                                    "label": "去看看",
                                    "uri": dict(anything_new)[comic_id]['url']
                                }
                            }
                        ]
                    }
                }
            }

            payload = {
                "to": GROUP_ID,
                "messages": [flex_message]
            }

            r = requests.post(LINE_MESSAGING_API, json=payload, headers=headers)

            if r.status_code != 200:
                raise AirflowFailException(f'Send line message fail: {r.status_code}, msg: {r.text}')
    else:
        raise AirflowFailException('LINE Channel Access Token not found')



def get_parameters(context):
    dag_run = context['dag_run']
    return dag_run.conf


with DAG('comic_init', default_args=default_args, tags=['comictotal'], schedule_interval=None) as dag:

    parse_new_comic = PythonOperator(
        task_id='parse_new_comic',
        python_callable=parse_new_comic,
        provide_context=True
    )
    get_read_history = PythonOperator(
        task_id='get_read_history',
        python_callable=process_metadata,
        op_args=['read'],
        provide_context=True
    )

    init_comic_info = PythonOperator(
        task_id='init_comic_info',
        python_callable=init_comic_info,
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
    parse_new_comic >> get_read_history >> init_comic_info
    init_comic_info >> update_read_history
    init_comic_info >> decide_what_to_do
    decide_what_to_do >> send_notification
    decide_what_to_do >> do_nothing
