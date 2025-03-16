from nonebot.plugin import PluginMetadata
from nonebot import get_driver

from zhenxun.configs.utils import PluginExtraData
from zhenxun.services.plugin_init import PluginInit

from .gClass import(
    g_pSqlManager,
    g_pJsonManager
)
from .command import (
    diuse_register
)

__plugin_meta = PluginMetadata(
    name = "真寻的农场",
    description = "快乐的农场时光",
    usage = """
        农场快乐时光
    """.strip(),
    extra = PluginExtraData(
        author="molanp",
        version="1.0",
        menu_type="群内小游戏",
    ).dict(),
)

#注册启动函数
driver = get_driver()

@driver.on_startup
async def start():
    #初始化数据库
    await g_pSqlManager.init()

    await g_pJsonManager.init()
