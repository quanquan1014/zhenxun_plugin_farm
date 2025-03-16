from nonebot_plugin_uninfo import Uninfo
from nonebot_plugin_alconna import Alconna, At, Image, Match, Text, UniMsg, on_alconna

import command

@diuse_register.handle()
async def _(session: Uninfo):
    uid = str(session.user.id)