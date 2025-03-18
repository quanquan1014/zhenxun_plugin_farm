from nonebot.rule import to_me
from nonebot_plugin_alconna import (Alconna, AlconnaQuery, Args, Match, Option,
                                    Query, Subcommand, on_alconna, store_true)
from nonebot_plugin_uninfo import Uninfo

from zhenxun.utils.message import MessageUtils

from .database import g_pSqlManager
from .drawImage import g_pDrawImage

diuse_register = on_alconna(
    Alconna("开通农场"),
    priority=5,
    rule=to_me(),
    block=True,
)

@diuse_register.handle()
async def _(session: Uninfo):
    uid = str(session.user.id)

    user = await g_pSqlManager.getUserInfoByUid(uid)

    if user:
        await MessageUtils.build_message("你已经有啦").send(reply_to=True)
    else:
        info = {"uid": uid, "name": "测试", "exp": 0, "point": 100}

        aaa = await g_pSqlManager.appendUserByUserInfo(info)

        await MessageUtils.build_message(str(aaa)).send(reply_to=True)

diuse_farm = on_alconna(
    Alconna(
        "我的农场",
        Option("--all", action=store_true),
        Subcommand("my-point", help_text="我的农场币"),
        Subcommand("plant-shop", help_text="种子商店"),
        Subcommand("buy-plant", Args["name?", str]["num?", int], help_text="购买种子"),
        Subcommand("my-plant", help_text="我的种子"),
        Subcommand("my-props", help_text="我的农场道具"),
        Subcommand("buy", Args["name?", str]["num?", int], help_text="购买道具"),
        Subcommand("use", Args["name?", str]["num?", int], help_text="使用道具"),
        Subcommand("gold-list", Args["num?", int], help_text="金币排行"),
    ),
    priority=5,
    rule=to_me(),
    block=True,
)

@diuse_farm.assign("$main")
async def _(session: Uninfo):
    uid = str(session.user.id)

    level = await g_pSqlManager.getUserLevelByUid(uid)
    if level <= 0:
        await MessageUtils.build_message("尚未开通农场").send()

        return None

    image = await g_pDrawImage.drawMyFarm(uid)

    await MessageUtils.build_message(image).send()

diuse_farm.shortcut(
    "我的农场币",
    command="我的农场",
    arguments=["my-point"],
    prefix=True,
)

@diuse_farm.assign("my-point")
async def _(session: Uninfo):
    uid = str(session.user.id)
    point = await g_pSqlManager.getUserPointByUid(uid)

    await MessageUtils.build_message(f"你的当前农场币为: {point}").send(reply_to=True)

diuse_farm.shortcut(
    "种子商店",
    command="我的农场",
    arguments=["plant-shop"],
    prefix=True,
)

@diuse_farm.assign("plant-shop")
async def _(session: Uninfo):
    uid = str(session.user.id)
    point = await g_pSqlManager.getUserPointByUid(uid)

    await MessageUtils.build_message(f"你的当前农场币为: {point}").send(reply_to=True)

diuse_farm.shortcut(
    "购买种子(?P<name>.*?)",
    command="我的农场",
    arguments=["buy-plant", "{name}"],
    prefix=True,
)

@diuse_farm.assign("buy-plant")
async def _(session: Uninfo, name: Match[str], num: Query[int] = AlconnaQuery("num", 1),):
    if not name.available:
        await MessageUtils.build_message(
            "请在指令后跟需要购买的种子名称"
        ).finish(reply_to=True)

    # result = await ShopManage.buy_prop(session.user.id, name.result, num.result)

    uid = str(session.user.id)
    point = await g_pSqlManager.getUserPointByUid(uid)

    await MessageUtils.build_message(f"你的当前农场币为: {point}").send(reply_to=True)



diuse_farm.shortcut(
    "种子商店",
    command="我的农场",
    arguments=["plant-shop"],
    prefix=True,
)

@diuse_farm.assign("plant-shop")
async def _(session: Uninfo):
    uid = str(session.user.id)
    point = await g_pSqlManager.getUserPointByUid(uid)

    await MessageUtils.build_message(f"你的当前农场币为: {point}").send(reply_to=True)
