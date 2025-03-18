from zhenxun.services.log import logger
from zhenxun.utils._build_image import BuildImage

from ..config import g_pJsonManager, g_sResourcePath
from ..database import g_pSqlManager


class CFarmManager:

    @classmethod
    async def drawFarm(cls, uid: str) -> bytes:
        """绘制农场

        Args:
            uid (str): 用户UID

        Returns:
            bytes: 返回绘制结果
        """
        soilNumber = await g_pSqlManager.getUserLevelByUid(uid)

        img = BuildImage(background=g_sResourcePath / "background/background.jpg")

        soilSize = g_pJsonManager.m_pSoil['size'] # type: ignore

        #TODO 缺少判断用户土地资源状况
        soil = BuildImage(background=g_sResourcePath / "soil/普通土地.png")
        await soil.resize(0, soilSize[0], soilSize[1])

        grass = BuildImage(background=g_sResourcePath / "soil/草土地.png")
        await grass.resize(0, soilSize[0], soilSize[1])

        soilPos = g_pJsonManager.m_pSoil['soil'] # type: ignore

        for key, value in soilPos.items():
            if soilNumber >= int(key):
                await img.paste(soil, (value['x'], value['y']))
            else:
                await img.paste(grass, (value['x'], value['y']))

        return img.pic2bytes()