import os
import time
import json
import logging
import re
import requests
import random
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
    'schedule_interval': f'{random.randint(0, 59)} * * * *',
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    'concurrency': 1,
    'max_active_runs': 1
}

LINE_NOTIFY_API = 'https://notify-api.line.me/api/notify'


def get_ep_number(title):
    result = re.findall("[-+]?[.]?[\d]+(?:,\d\d\d)*[\.-]?\d*(?:[eE][-+]?\d+)?", title)
    if len(result) > 0:
        return result[0]
    else:
        return None


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
    comic_keys = list(all_comic_info.keys())
    last_module = None
    for comic_id in sorted(comic_keys, key=lambda _: random.random()):
        comic_info = all_comic_info[comic_id]
        ep_set = set([get_ep_number(ep['title']) for comic in comic_info['source'] for ep in comic['episodes']])
        if (datetime.now() - timedelta(hours=12)).timestamp() < int(comic_info['last_update']):
            print(f'{comic_id} is already updated in last 12 hours')
            continue
        for comic in comic_info['source']:
            try:
                mission = Mission(url=comic['url'])

                if last_module == mission.module.name:
                    time.sleep(random.randint(5, 20))
                else:
                    last_module = mission.module.name

                Analyzer(mission).analyze()

                old_eps = EpisodeList([Episode(**e) for e in comic['episodes']])
                has_new_ep = False
                for ep in reversed(mission.episodes):
                    if old_eps.add(ep):
                        ep_info = {
                            "comic_title": mission.title,
                            "chapter": ep.title,
                            "url": ep.url
                        }
                        epi_number = get_ep_number(ep.title)
                        if len(comic_info['source']) > 1:
                            if epi_number not in ep_set:
                                has_new_ep = True
                                ep_set.add(epi_number)
                                if comic_id not in anything_new:
                                    anything_new[comic_id] = [ep_info]
                                    comic_info['latest_chapter'] = epi_number
                                else:
                                    anything_new[comic_id].append(ep_info)
                            else:
                                print(f'{comic_id} latest ep already released, new: {ep.title}, record: {comic_info["latest_chapter"]}')
                        else:
                            has_new_ep = True
                            if comic_id not in anything_new:
                                anything_new[comic_id] = [ep_info]
                                comic_info['latest_chapter'] = epi_number
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

        for comic_id in dict(anything_new):
            for comic in anything_new[comic_id]:
                # 取得漫畫縮圖 URL
                thumbnail_url = all_comic_info[comic_id].get('thumbnail_url', None)

                # 根據是否有縮圖決定發送的消息類型
                if thumbnail_url:
                    # 有縮圖時使用 Flex Message
                    message = {
                        "type": "flex",
                        "altText": f"{comic_id} 更新了！最新話: {comic['chapter']}",
                        "contents": {
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "url": thumbnail_url,
                                "size": "full",
                                "aspectRatio": "20:13",
                                "aspectMode": "cover",
                                "action": {
                                    "type": "uri",
                                    "uri": comic['url']
                                }
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": comic_id,
                                        "weight": "bold",
                                        "size": "xl"
                                    },
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "margin": "md",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "更新啦 ！！！",
                                                "size": "sm",
                                                "color": "#999999",
                                                "margin": "md",
                                                "flex": 0
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "vertical",
                                        "margin": "lg",
                                        "spacing": "sm",
                                        "contents": [
                                            {
                                                "type": "box",
                                                "layout": "baseline",
                                                "spacing": "sm",
                                                "contents": [
                                                    {
                                                        "type": "text",
                                                        "text": "最新話",
                                                        "color": "#aaaaaa",
                                                        "size": "sm",
                                                        "flex": 1
                                                    },
                                                    {
                                                        "type": "text",
                                                        "text": comic['chapter'],
                                                        "wrap": True,
                                                        "color": "#666666",
                                                        "size": "sm",
                                                        "flex": 5
                                                    }
                                                ]
                                            }
                                        ]
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
                                        "height": "sm",
                                        "action": {
                                            "type": "uri",
                                            "label": "去看看",
                                            "uri": comic['url']
                                        }
                                    }
                                ],
                                "flex": 0
                            }
                        }
                    }
                else:
                    # 沒有縮圖時使用文字消息
                    message = {
                        "type": "text",
                        "text": f"{comic_id} 更新啦 ！！！\n最新話: {comic['chapter']}\n{comic['url']}"
                    }

                payload = {
                    "to": GROUP_ID,
                    "messages": [message]
                }

                r = requests.post(LINE_MESSAGING_API, json=payload, headers=headers)

                if r.status_code != 200:
                    raise AirflowFailException(f'Send line message fail: {r.status_code}, msg: {r.text}')
    else:
        raise AirflowFailException('LINE Channel Access Token not found')


with DAG('comic_update_pipeline', default_args=default_args, tags=['comictotal'], schedule_interval=None, catchup=False, max_active_runs=1,concurrency=2) as dag:

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
