from .component import Component
from .text import ComponentText
from .chart import ComponentChart
from .image import ComponentImage
from .youtube_video import ComponentYouTubeVideo

components = {
    "text": ComponentText,
    "chart": ComponentChart,
    "image": ComponentImage,
    "youtube_video": ComponentYouTubeVideo,
}

component_api_json_description = ""
for key, component_class in components.items():
    component_api_json_description += component_class.json_description() + "\n"
