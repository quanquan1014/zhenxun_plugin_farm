from ast import arg

from zhenxun.services.log import logger
from zhenxun.utils._build_image import BuildImage

from .config import g_pJsonManager, g_sResourcePath
from .database import g_pSqlManager


class CDrawImageManager:

    @classmethod
    async def drawMyFarm(cls, uid: str) -> bytes:
        """绘制我的农场

        Args:
            uid (str): 用户UID

        Returns:
            bytes: 返回绘制结果
        """
        # soilNumber = await self.m_pSql.getUserLevelByUid(uid)
        soilNumber = 1

        img = BuildImage(background=g_sResourcePath / "background/background.jpg")

        soil = BuildImage(background=g_sResourcePath / "soil/普通土地.png")
        await soil.resize(0, 229, 112)

        grass = BuildImage(background=g_sResourcePath / "soil/草土地.png")
        await grass.resize(0, 229, 112)

        soilPos = g_pJsonManager.m_pSoil['soil']

        for key, value in soilPos.items():
            if soilNumber >= int(key):
                await img.paste(soil, (value['x'], value['y']), center_type="center")
            else:
                await img.paste(grass, (value['x'], value['y']), center_type="center")

        return img.pic2bytes()

g_pDrawImage = CDrawImageManager()
