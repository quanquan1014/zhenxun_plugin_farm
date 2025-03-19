from numpy import arange

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
        isFirst = True
        for index, level in enumerate(soilUnlock):
            x = soilPos[str(index + 1)]['x']
            y = soilPos[str(index + 1)]['y']

            #如果土地已经到达对应等级
            if soilNumber >= int(level):
                await img.paste(soil, (x, y))

                #TODO 缺少判断土地上是否有农作物
                plant = BuildImage(background=g_sResourcePath / "plant/basic/0.png")
                await plant.resize(0, 35, 58)
                await img.paste(plant, (x + 100, y + 50))
            else:
                await img.paste(grass, (x, y))

                if isFirst:
                    isFirst = False

                    #首次添加扩建图片
                    expansion = BuildImage(background=g_sResourcePath / "background/expansion.png")
                    await expansion.resize(0, 69, 69)
                    await img.paste(expansion, (x + 85, y + 20))

        return img.pic2bytes()

    @classmethod
    async def getUserPlantByUid(cls, uid: str) -> bytes:
        """获取用户种子仓库

        Args:
            uid (str): 用户Uid

        Returns:
            bytes: 返回图片
        """

        data_list = []
        column_name = [
            "-",
            "种子名称",
            "数量",
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
                plantName, count = item.split('|', 1)  # 分割一次，避免多竖线问题
                try:
                    plantInfo = g_pJsonManager.m_pPlant['plant'][plantName] # type: ignore

                    icon = ""
                    icon_path = g_sResourcePath / f"plant/{plantName}/icon.png"
                    if icon_path.exists():
                        icon = (icon_path, 33, 33)

                    if plantInfo['again'] == True:
                        sell = "可以"
                    else:
                        sell = "不可以"

                    data_list.append(
                        [
                            icon,
                            plantName,
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

    @classmethod
    async def sowing(cls, uid: str, name: str, num: int = 1) -> str:
        """播种

        Args:
            uid (str): 用户Uid
            name (str): 播种种子名称
            num (int, optional): 播种数量

        Returns:
            str:
        """
        plant = await g_pSqlManager.getUserPlantByUid(uid)

        if plant == None:
            return "你的种子仓库是空的，快去买点吧！"

        for item in plant.split(','):
            if '|' in item:
                plantName, count = item.split('|', 1)  # 分割一次，避免多竖线问题

                #判断仓库是否有当前播种种子
                if plantName == name:
                    count = int(count)

                    #获取用户解锁多少块地
                    soilName = ""
                    soilNumber = await g_pSqlManager.getUserSoilByUid(uid)
                    #遍历地块，查看地块是否可以播种
                    for i in arange(1, soilNumber + 1):
                        if count > 0:
                            soilName = f"soil{str(i)}"
                            #如果可以播种
                            if await g_pSqlManager.getUserSoilStatusBySoilID(uid, soilName):
                                count -= 1
                                await g_pSqlManager.updateUserSoilStatusBySowing(uid, soilName, plantName)
                                return f"播种{plantName}成功！"
        return "播种失败"

g_pFarmManager = CFarmManager()
