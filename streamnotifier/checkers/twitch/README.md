## TwitchStreamNotifyBot

This uses Twitch API to determine stream status and broadcast to supported respective platforms.

Primarily built for [Cyannyan](https://cyannyan.com)'s Twitch stream notifications.

---

## Usage

### Parameters

```
usage: __main__.py [-h] [-p CONFIG_PATH] [-c CACHE_PATH] [-t]

optional arguments:
  -h, --help            show this help message and exit
  -p CONFIG_PATH, --path CONFIG_PATH
                        Path to configuration json file. Default path is
                        'configuration.json' adjacent to this script
  -c CACHE_PATH, --cache CACHE_PATH
                        Path where cache file will be. Default path is
                        'cache.json' adjacent to this script
  -t, --test            Enable test mode, this does not actually push to
                        platforms.
```

### Installation 

Install requirements by:
```
python3 -m pip install -r requirements.txt
```

### Execution

And run `__main__.py` either by:

```
python3 __main__.py
```

```
python3 TwitchStreamNotifyBot
```

But I recommend making this into systemd Service or Docker image for continuous execution after making sure configuration works flawlessly.

---

## Config

Any misconfiguration will render respective push platform unusable. Please keep eye on log output for few runs.

```json
{
  "channel name": "<Twitch_channel_name>",
  "polling api": {
    "twitch app id": "<twitch_app_id_here>",
    "twitch app secret": "<twitch_app_secret_here>"
  },
  "push methods": {
    "discord": {
      "webhook url": "<discord_webhook_url>",
      "content": "<@&discord_role_id> Live now! {}\nStarted at: {started_at}\nGame: {game_name}"
    },
    "telegram": {
      "token": "<telegram_bot_token>",
      "chat id": ["<telegram_chat_id_here_as_integer>"],
      "content": "Test Push {link}\nStarted at: {started_at}\nGame: {game_name}"
    },
    "twitter": {
      "api key": "<api key>",
      "api secret key": "<api secret key>",
      "bearer token": "Unused for now",
      "access token": "<access token>",
      "access token secret": "<access token secret>",
      "content": "Bot Twitter push test\n\n{link}\nStarted at: {started_at}\nGame: {game_name}"
    },
    "reddit": {
      "reddit api": "Not_available_yet",
      "content": "add_some_mention_thingy_here {link}"
    }
  }
}

```

---

## Config descriptions

Contents will be formatted with keywords.

Available `content` format keywords are:
```python
# General keywords
'game_name': 'osu!'
'title': 'Road to 5* | Join Multi! | VTuber Cyan'
'link': 'https://www.twitch.tv/cyannyan39'
'started_at': '2021-08-03T02:05:11Z'

# included, but not frequently used.
'game_id': '21465'
'id': '43109063245'
'is_mature': False
'language': 'en'
'tag_ids': ['6ea6bca4-4712-4ab9-a906-e3336a9d8039']
'thumbnail_url': 'https://static-cdn.jtvnw.net/previews-ttv/live_user_cyannyan39-{width}x{height}.jpg'
'type': 'live'
'user_id': '585389049'
'user_login': 'cyannyan39'
'user_name': 'CyanNyan39'
'viewer_count': 1
```

These keywords are formatted by `str.format()`. For example:
```python
"Test Push {link}\nStarted at: {started_at}\nGame: {game_name}"
```

Will be formatted like:

```python
message = "Test Push {link}\nStarted at: {started_at}\nGame: {game_name}".format(**dict)
```

Then it becomes

```python
message = "Test Push https://www.twitch.tv/cyannyan39\nStarted at: 2021-08-03T02:05:11Z\nGame: osu!"
```

---

## Warning

- Discord Webhook URL will be verified by sending and removing sent message at startup. This is normal behavior.


- Make sure Twitter app has permission to write(and read if possible)

    ![image](https://user-images.githubusercontent.com/26041217/128051987-ea4a6749-8668-411f-a94f-9a22d0236b7b.png)


- Twitter *DOES NOT* allow same content, and since the only thing that is unique to every Twitch streams are `started_at`, it is recommended to add it in content.

---

## Example output

### Discord

  ![image](https://user-images.githubusercontent.com/26041217/127901726-b4a4333f-f900-4e3a-94c6-21b9b919b5cc.png)

---

### Telegram

  ![image](https://user-images.githubusercontent.com/26041217/127901680-96beb0c9-a9ff-4eb1-acf5-682dd8a76113.png)

---

### Twitter

  ![image](https://user-images.githubusercontent.com/26041217/127901434-e4528f97-7326-4bd0-ad7a-27b8c8c8f961.png)
