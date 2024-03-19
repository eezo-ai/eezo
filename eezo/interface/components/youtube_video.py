from .component import Component


class ComponentYouTubeVideo(Component):
    type = "youtube_video"

    def __init__(self, video_id):
        super().__init__()
        self.video_id = video_id

    def to_dict(self):
        return {"type": self.type, "video_id": self.video_id}
