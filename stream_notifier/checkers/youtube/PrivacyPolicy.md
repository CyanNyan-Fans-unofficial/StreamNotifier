### What information do you collect?

Collects information about Currently Active livestream, and information about the livestream if active.
This information is not stored anywhere.

This includes following fields:
- [LiveBroadcasts.list](https://developers.google.com/youtube/v3/live/docs/liveBroadcasts/list): snippet, status

### How do you use the information?

- Primarily for checking if authorized channel is currently live or not
- If live, uses fields at [liveBroadcasts resource](https://developers.google.com/youtube/v3/live/docs/liveBroadcasts#resource) for pushing notifications to configured location.

### What information do you share?

No information is shared or stored.

Only [liveBroadcasts resource](https://developers.google.com/youtube/v3/live/docs/liveBroadcasts#resource) fields that was formatted on [configuration file](https://github.com/jupiterbjy/StreamNotifier/tree/main/YoutubeStreamNotifyBot#config) will be sent to configured platform as form of *Notification*.
