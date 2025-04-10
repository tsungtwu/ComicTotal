import hashlib
import json
from comiccrawler.episode import Episode


def get_ep_path(misson):
    pass

def get_mission_id(mission):
	"""Use title and sha1 of URL as mission id"""
	return "{title}_{sha1}".format(
		title=mission.title,
		sha1=hashlib.sha1(mission.url.encode("utf-8")).hexdigest()[:6]
	)

def load_episodes(mission):
    mission_id = id(mission)
    if not mission.episodes:
        eps = json.load(get_ep_path(mission))
        if eps:
            mission.episodes = [Episode(**e) for e in eps]


