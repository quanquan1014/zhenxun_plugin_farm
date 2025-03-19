from zhenxun.services.log import logger
from zhenxun.utils._build_image import BuildImage
from zhenxun.utils.image_utils import ImageTemplate

from ..config import g_pJsonManager, g_sResourcePath
from ..database import g_pSqlManager


class CFarmManager:

    @classmethod
    async def drawFarmByUid(cls, uid: str) -> bytes:
        """绘制用户农场

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
        soilUnlock = g_pJsonManager.m_pLevel['soil'] # type: ignore

        x = 0
        y = 0
        for index, level in enumerate(soilUnlock):
            x = soilPos[str(index + 1)]['x']
            y = soilPos[str(index + 1)]['y']

            if soilNumber >= int(level):
                await img.paste(soil, (x, y))

                #缺少判断土地上是否有农作物
                plant = BuildImage(background=g_sResourcePath / "plant/basic/0.png")
                await plant.resize(0, 35, 58)
                await img.paste(plant, (x + 3, y + 3))
            else:
                await img.paste(grass, (x, y))

        return img.pic2bytes()

    @classmethod
    async def getUserPlantByUid(cls, uid: str) -> bytes:
        data_list = []
        column_name = [
            "-",
            "种子名称",
            "数量"
            "收获经验",
            "收获数量",
            "成熟时间（分钟）",
            "收获次数",
            "再次成熟时间（分钟）",
            "是否可以上架交易行"
        ]

        plant = await g_pSqlManager.getUserPlantByUid(uid)

        if plant == None:
            result = await ImageTemplate.table_page(
                "种子仓库",
                "播种示例：@小真寻 播种 大白菜",
                column_name,
                data_list,
            )

            return result.pic2bytes()

        sell = ""

        for item in plant.split(','):
            if '|' in item:
                plant_name, count = item.split('|', 1)  # 分割一次，避免多竖线问题
                try:
                    plantInfo = g_pJsonManager.m_pPlant['plant'][plant_name] # type: ignore

                    icon = ""
                    icon_path = g_sResourcePath / f"plant/{plant_name}/icon.png"
                    if icon_path.exists():
                        icon = (icon_path, 33, 33)

                    if plantInfo['again'] == True:
                        sell = "可以"
                    else:
                        sell = "不可以"

                    data_list.append(
                        [
                            icon,
                            plant_name,
                            count,
                            plantInfo['experience'],
                            plantInfo['harvest'],
                            plantInfo['time'],
                            plantInfo['crop'],
                            plantInfo['again'],
                            sell
                        ]
                    )

                except Exception as e:
                    continue

        result = await ImageTemplate.table_page(
            "种子商店",
            "购买示例：@小真寻 购买种子 大白菜 5",
            column_name,
            data_list,
        )

        return result.pic2bytes()

g_pFarmManager = CFarmManager()
