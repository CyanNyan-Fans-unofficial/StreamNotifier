from loguru import logger

from .youtube_api_client import build_client


class RequestInstance:
    color = 'ff0000'
    check_interval = 10

    def __init__(self, config):
        # read config meow
        client_secret = config["client_secret"]
        token = config.get("token")

        self.client = build_client(client_secret=client_secret, token=token)

        logger.info("Application successfully authorized.")

    async def run_check(self):
        active = self.client.get_active_user_broadcasts(max_results=1)
        if active:
            # gotcha! there's active stream
            stream = active[0]

            logger.debug("Found Active stream: {}", stream)
            result = stream.as_dict()

            if result["description"]:
                description = result["description"].strip().split("\n")
                result["description_first_line"] = description[0]

            return result

    def verify_push(self, last_notified, current_info):
        if current_info["id"] == last_notified.get("id"):
            return False

        if current_info["title"] == self.last_notified.get("title"):
            raise ValueError("YouTube stream title did not change!")

        if current_info["privacy_status"] == "private":
            raise ValueError("YouTube Stream is private!")

        return True

    def summary(self, info):
        return {
            "Started": info['actual_start_time'],
            "Title": info['title'],
            "Privacy": info['privacy_status'],
            "link": info['link'],
            "Live": info['life_cycle_status']
        }
