from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from zhenxun.configs.utils import Command, PluginExtraData
from zhenxun.services.log import logger
from zhenxun.utils.message import MessageUtils

from .command import diuse_farm, diuse_register
from .config import g_pJsonManager
from .database import g_pSqlManager
from .farm.farm import g_pFarmManager
from .farm.shop import g_pShopManager

__plugin_meta__ = PluginMetadata(
    name="真寻农场",
    description="快乐的农场时光",
    usage="""
    你也要种地?
    指令：
        at 开通农场
        我的农场
        我的农场币
        种子商店
        购买种子 [作物/种子名称] [数量]
        我的种子
        播种 [作物/种子名称] [数量]
        收获
        铲除
        我的作物
        出售作物 [作物/种子名称] [数量]
        偷菜 at
        开垦
        购买农场币 [数量] 金币转换农场币比率是 1 : 2
    """.strip(),
    extra=PluginExtraData(
        author="Art_Sakura",
        version="1.0",
        commands=[Command(command="我的农场")],
        menu_type="群内小游戏"
    ).to_dict(),
)
driver = get_driver()


# 构造函数
@driver.on_startup
async def start():
    # 初始化数据库
    await g_pSqlManager.init()

    # 初始化读取Json
    await g_pJsonManager.init()

# 析构函数
@driver.on_shutdown
async def shutdown():
    await g_pSqlManager.cleanup()
