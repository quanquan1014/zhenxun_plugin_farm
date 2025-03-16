from nonebot.rule import to_me
from nonebot_plugin_uninfo import Uninfo
from nonebot_plugin_alconna import Alconna, on_alconna, Text

from zhenxun.services.log import logger


from .gClass import(
    g_pSqlManager
)

diuse_register = on_alconna(
    Alconna("注册空间"),
    priority = 5,
    rule=to_me(),
    block = True,
)

@diuse_register.handle()
async def _(session: Uninfo):
    uid = str(session.user.id)

    user = await g_pSqlManager.getUserByUid(uid)

    if user:
        await diuse_register.send(Text("你已经有啦"), reply_to=True)
    else:
        info = {'uid' : uid, 'name' : '测试', 'level' : 1, 'point' : 0}

        aaa = await g_pSqlManager.appendUserByUserInfo(info)
        await diuse_register.send(Text(str(aaa)), reply_to=True)