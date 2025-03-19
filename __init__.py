from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import PluginExtraData
from zhenxun.services.log import logger
from zhenxun.utils.message import MessageUtils

from .command import diuse_farm, diuse_register
from .config import g_pJsonManager
from .database import g_pSqlManager
from .farm.farm import g_pFarmManager
from .farm.shop import g_pShopManager

__plugin_meta = PluginMetadata(
    name="真寻的农场",
    description="快乐的农场时光",
    usage="""
        农场快乐时光
    """.strip(),
    extra=PluginExtraData(
        author="molanp",
        version="1.0",
        menu_type="群内小游戏",
    ).dict(),
)

driver = get_driver()


# 构造函数
@driver.on_startup
async def start():
    # 初始化数据库
    await g_pSqlManager.init()

    # 初始化读取Json
    await g_pJsonManager.init()

    aaa = await g_pFarmManager.sowing("1754798088", "胡萝卜", 1)
    logger.info(aaa)

# 析构函数
@driver.on_shutdown
async def shutdown():
    await g_pSqlManager.cleanup()
