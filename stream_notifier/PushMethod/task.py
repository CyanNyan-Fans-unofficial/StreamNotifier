class PushTask:
    def __init__(self, name, comment, push_instance, content, test_mode=False):
        self.name = name
        self.comment = comment
        self.instance = push_instance
        self.content = content
        self.test_mode = test_mode

    async def send(self):
        if not self.test_mode:
            await self.instance.send(self.content)
