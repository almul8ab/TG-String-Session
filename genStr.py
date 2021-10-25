import asyncio

from bot import bot, HU_APP
from pyromod import listen
from asyncio.exceptions import TimeoutError

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired
)

API_TEXT = """Hi, {}.اهلا وسهلا بك في بوت استخراج الكود سترنك الخاص بسورس جيبثون
ركز معي
الان ارسل لي `API_ID` ارسل `APP_ID` وانتضر."""
HASH_TEXT = "الان ارسل لي `API_HASH`.\n\nاو اضغط /cancel للخروج."
PHONE_NUMBER_TEXT = (
    "الان ارسل لي رقم موبايلك الي رابط عليه حسابك التليجرام مع رمز الدولة على سبيل المثال. \n"
    "**+14154566376**\n\n"
    "او اضغظ /cancel لأنهاء الاستخراج."
)

@bot.on_message(filters.private & filters.command("start"))
async def genStr(_, msg: Message):
    chat = msg.chat
    api = await bot.ask(
        chat.id, API_TEXT.format(msg.from_user.mention)
    )
    if await is_cancel(msg, api.text):
        return
    try:
        check_api = int(api.text)
    except Exception:
        await msg.reply("`API_ID` خطأ.\nارجع دوس /start وعيد من جديد.")
        return
    api_id = api.text
    hash = await bot.ask(chat.id, HASH_TEXT)
    if await is_cancel(msg, hash.text):
        return
    if not len(hash.text) >= 30:
        await msg.reply("`API_HASH` خطأ.\ارجع دوس /start وعيد من جديد.")
        return
    api_hash = hash.text
    while True:
        number = await bot.ask(chat.id, PHONE_NUMBER_TEXT)
        if not number.text:
            continue
        if await is_cancel(msg, number.text):
            return
        phone = number.text
        confirm = await bot.ask(chat.id, f'`Is "{phone}" correct? (y/n):` \n\nSend: `y` (If Yes)\nSend: `n` (If No)')
        if await is_cancel(msg, confirm.text):
            return
        if "y" in confirm.text:
            break
    try:
        client = Client("my_account", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await bot.send_message(chat.id ,f"**خطا ابني اتأكد من الاكواد:** `{str(e)}`\nارجع دوس /start وعيد الشغل من جديد.")
        return
    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    try:
        code = await client.send_code(phone)
        await asyncio.sleep(1)
    except FloodWait as e:
        await msg.reply(f"فحطتني هواي تكرر انتضر {e.x} ثانية")
        return
    except ApiIdInvalid:
        await msg.reply("API ID و API Hash ثنينهن خطأ.\n\nدوس /start وارجع من جديد.")
        return
    except PhoneNumberInvalid:
        await msg.reply("رقم موبايلك غلط تأكد منه لاتستعجل مراح يطير البوت.\n\nارجع دوس /start وابدي شغل من جديد حجي.")
        return
    try:
        otp = await bot.ask(
            chat.id, ("اجاك كود ع التلي مالتك مكون من ٥ ارقام دزهن هنا, "
                      "بس باع من تكتبهن خلي بين كل رقم مسافة مثل  `1 2 3 4 5` \n\n"
                      "هسه شجاك وصلت للنهاية وخطأت ارجع دوس /restart وابدي شغل من جديد عزيزي.\n"
                      "دوس /cancel to حتى تنهي كلشي."), timeout=300)

    except TimeoutError:
        await msg.reply("Time limit reached of 5 min.\nPress /start to Start again.")
        return
    if await is_cancel(msg, otp.text):
        return
    otp_code = otp.text
    try:
        await client.sign_in(phone, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await msg.reply("الكود خطأ لصير اثول.\n\nدوس /start وارجع عيد من جديد.")
        return
    except PhoneCodeExpired:
        await msg.reply("الكود صار اكسباير يعني انتهت صلاحيته.\n\nدوس /start وارجع عيد من جديد.")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                chat.id, 
                "حسابك مسويله تأكد بخطوتين مو ؟.\nلعد دزلي الباسورد ولتحجي حجي زايد.\n\nدوس /cancel حتى تنهي شغلك.",
                timeout=300
            )
        except TimeoutError:
            await msg.reply("`Time limit reached of 5 min.\n\nPress /start to Start again.`")
            return
        if await is_cancel(msg, two_step_code.text):
            return
        new_code = two_step_code.text
        try:
            await client.check_password(new_code)
        except Exception as e:
            await msg.reply(f"**خطااااا:** `{str(e)}`")
            return
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"#PYROGRAM #STRING_SESSION\n\n```{session_string}``` \n\nBy [@StringSessionGen_Bot](tg://openmessage?user_id=1472531255) \nA Bot By @Discovery_Updates")
        await client.disconnect()
        text = "تمت بحمد الله تعالى انتهينا من الاستخراج.\nدوس على الزر حتى يوديك للكود."
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="اريد اشوف الكود", url=f"tg://openmessage?user_id={chat.id}")]]
        )
        await bot.send_message(chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return


@bot.on_message(filters.private & filters.command("restart"))
async def restart(_, msg: Message):
    await msg.reply("Restarted Bot!")
    HU_APP.restart()


@bot.on_message(filters.private & filters.command("help"))
async def restart(_, msg: Message):
    out = f"""
Hi, {msg.from_user.mention}. This is Pyrogram Session String Generator Bot. \
I will give you `STRING_SESSION` for your UserBot.

It needs `API_ID`, `API_HASH`, Phone Number and One Time Verification Code. \
Which will be sent to your Phone Number.
You have to put **OTP** in `1 2 3 4 5` this format. __(Space between each numbers!)__

**NOTE:** If bot not Sending OTP to your Phone Number than send /restart Command and again send /start to Start your Process. 

Must Join Channel for Bot Updates !!
"""
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('كروب الدعم', url='https://t.me/jepthon1'),
                InlineKeyboardButton('🙋🏻المطور', url='https://t.me/lMl10l')
            ],
            [
                InlineKeyboardButton('قناة التحديثات 🧸', url='https://t.me/Jepthon'),
            ]
        ]
    )
    await msg.reply(out, reply_markup=reply_markup)


async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("كافي چلبت دطلع.")
        return True
    return False

if __name__ == "__main__":
    bot.run()
