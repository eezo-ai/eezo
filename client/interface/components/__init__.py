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
