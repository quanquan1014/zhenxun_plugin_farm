from zhenxun.utils._build_image import BuildImage

from .config import g_sResourcePath


class CDrawImageManager:
    @classmethod
    async def drawMyFarm(cls) -> bytes:
        img = BuildImage(background=g_sResourcePath / "background/background.jpg")

        return img.pic2bytes()
