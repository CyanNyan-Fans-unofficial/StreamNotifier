## YoutubeStreamNotifyBot

This uses Youtube API to determine stream status and broadcast to supported respective platforms.

Primarily built for [Cyannyan](https://cyannyan.com)'s Youtube stream notifications.

***This is only meant to be used by streamer due to API limitations.***

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

Additionally, unless I explicitly provided client secret json file,
you'll have to generate and download client secret json file from [Google console](https://console.cloud.google.com/apis/credentials).

![image](https://user-images.githubusercontent.com/26041217/128898306-a3c23e68-5d67-4c17-b4bd-77ab6362dc10.png)

### Execution

And run `__main__.py` either by:

```
python3 __main__.py
```

```
python3 YoutubeStreamNotifyBot
```

But I recommend making this into systemd Service or Docker image for continuous execution after making sure configuration works flawlessly.

---

## Config

Any misconfiguration will render respective push platform unusable. Please keep eye on log output for few runs.

```json
{
  "client secret file path": "client_secret_location",
  "push methods": {
    "discord": {
      "webhook url": "<discord_webhook_url>",
      "content": "Test push\n\ntitle: [{title}]\ndescription: [{description}]\ntype: [{privacy_status}]\nurl: [{link}]"
    },
    "telegram": {
      "token": "<telegram_bot_token>",
      "chat id": ["<telegram_chat_id_here_as_integer>"],
      "content": "Test push\n\ntitle: [{title}]\ndescription: [{description}]\ntype: [{privacy_status}]\nurl: [{link}]"
    },
    "twitter": {
      "api key": "<api key>",
      "api secret key": "<api secret key>",
      "bearer token": "Unused for now",
      "access token": "<access token>",
      "access token secret": "<access token secret>",
      "content": "Test push\n\ntitle: [{title}]\ndescription: [{description}]\ntype: [{privacy_status}]\nurl: [{link}]"
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
{
  'title': 'Testing API-2',
  'description': 'Testing API',
  'link': 'https://www.youtube.com/watch?v=xXKDbi5LbP4',
  
  'actual_end_time': None,
  'actual_start_time': datetime.datetime(2021, 8, 10, 12, 35, 50, tzinfo=tzutc()),
  'channel_id': 'UC1Cw26goXoneW-qK5aXyjWQ',
  'etag': 'mGXq7KhcbDmSqA7xsTFh_X0jtIY',
  'id': 'xXKDbi5LbP4',
  'is_default_broadcast': False,
  'is_live': True,
  'kind': 'youtube#liveBroadcast',
  'life_cycle_status': 'live',
  'live_chat_id': 'KicKGFVDMUN3MjZnb1hvbmVXLXFLNWFYeWpXURILeFhLRGJpNUxiUDQ',
  'made_for_kids': False,
  'privacy_status': 'private',
  'published_at': datetime.datetime(2021, 8, 10, 12, 35, 36, tzinfo=tzutc()),
  'recording_status': 'recording',
  'scheduled_end_time': None,
  'scheduled_start_time': datetime.datetime(2021, 8, 10, 12, 35, 32, tzinfo=tzutc()),
  'self_declared_made_for_kids': False,
}
```

These keywords are formatted by `str.format()`. For example:
```python
"Test push\n\ntitle: [{title}]\ndescription: [{description}]\ntype: [{privacy_status}]\nurl: [{link}]"
```

Will be formatted like:

```python
message = "Test push\n\ntitle: [{title}]\ndescription: [{description}]\ntype: [{privacy_status}]\nurl: [{stream_url}]".format(**dict)
```

Then it becomes

```python
message = "Test push\n\ntitle: [Notification Testing-1]\ndescription: [Testing notifications]\ntype: [public]\nurl: [https://www.youtube.com/watch?v=LE6VO0KNbuY]"
```

---

## Warning

- Discord Webhook URL will be verified by sending and removing sent message at startup. This is normal behavior.


- Make sure Twitter app has permission to write(and read if possible)

    ![image](https://user-images.githubusercontent.com/26041217/128051987-ea4a6749-8668-411f-a94f-9a22d0236b7b.png)

---

## Example output

### Discord

  ![image](https://user-images.githubusercontent.com/26041217/128896757-b158bcb6-0482-4a0c-8e61-669996e9fad8.png)

---

### Telegram

  ![image](https://user-images.githubusercontent.com/26041217/128896569-d1f06c5e-4162-4834-bac8-f03ca805020e.png)

---

### Twitter

  ![image](https://user-images.githubusercontent.com/26041217/128896542-25708fc0-2912-43a1-b817-5105b7f2d189.png)
