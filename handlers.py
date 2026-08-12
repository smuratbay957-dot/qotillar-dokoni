from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    URLInputFile,
    WebAppInfo,
)

import codes
import db
import products
from config import ADMIN_ID, START_BALANCE, WEB_URL

router = Router()

TIER_NAMES = {
    1: ("🗡️ 1-DARAJA", "Qotillik qurollari"),
    2: ("🕵️ 2-DARAJA", "Josus narsalari"),
    3: ("🧹 3-DARAJA", "Tozalash narsalar"),
}


def web_button():
    if WEB_URL.startswith("https"):
        return [
            InlineKeyboardButton(
                text="🌐 Saytga kirish",
                web_app=WebAppInfo(url=WEB_URL),
            )
        ]
    return [InlineKeyboardButton(text="🌐 Saytga kirish", url=WEB_URL)]


def main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏪 Dokonga kirish", callback_data="shop")],
            [
                InlineKeyboardButton(text="🎨 Kodlar", callback_data="codes"),
                InlineKeyboardButton(text="💰 Balans", callback_data="balance"),
            ],
            [InlineKeyboardButton(text="🎒 Inventar", callback_data="inventory")],
            web_button(),
        ]
    )


def shop_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{TIER_NAMES[1][0]} // {TIER_NAMES[1][1]}",
                    callback_data="tier:1",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{TIER_NAMES[2][0]} // {TIER_NAMES[2][1]}",
                    callback_data="tier:2",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{TIER_NAMES[3][0]} // {TIER_NAMES[3][1]}",
                    callback_data="tier:3",
                )
            ],
            [InlineKeyboardButton(text="✍️ Adminga yozish", callback_data="write_admin")],
            [InlineKeyboardButton(text="📦 Buyurtma berish", callback_data="order_request")],
            [InlineKeyboardButton(text="📦 Buyurtmalarim", callback_data="my_orders")],
            [InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="menu")],
        ]
    )


def back_to_shop_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Do'konga qaytish", callback_data="shop")]]
    )


def menu_text(user):
    return (
        "🏪 *QOTILLAR DO'KONI*\n\n"
        f"Kod: {codes.info(user['code'])}\n"
        f"💰 Balans: {user['balance']} kredit\n\n"
        "Nima qilamiz?"
    )


async def ensure_registered(cb: CallbackQuery):
    db.ensure_user(cb.from_user.id, cb.from_user.first_name, START_BALANCE)
    user = db.get_user(cb.from_user.id)
    if not user["code"]:
        await cb.answer("Avval kod tanlang! /start bosing.", show_alert=True)
        return None
    return user


@router.message(CommandStart())
async def cmd_start(message: Message):
    print(f"START RECEIVED: from={message.from_user.id}", flush=True)
    db.ensure_user(message.from_user.id, message.from_user.first_name, START_BALANCE)
    user = db.get_user(message.from_user.id)
    if not user["code"]:
        await message.answer(
            "🎬 *QOTILLAR DO'KONI* botiga xush kelibsiz!\n\n"
            "Bu 'A Shop for Killers' kinosi asosidagi *soxta o'yin* — "
            "hammasi fantastika, faqat ko'ngil ochish uchun. 😄\n\n"
            "Kino'dagi kabi Murthehelp do'koniga kirdingiz.\n"
            "Admin tomonidan berilgan kodingiz bilan kiring:\n"
            "`/kirish <kod>`\n\n"
            "Kodingiz bo'lmasa — admin bilan bog'laning."
        )
    else:
        await message.answer(
            menu_text(user),
            reply_markup=main_menu_keyboard(),
        )


@router.message(Command("kodlar"))
async def cmd_codes(message: Message):
    db.ensure_user(message.from_user.id, message.from_user.first_name, START_BALANCE)
    await message.answer(
        codes.all_info(),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="menu")]]
        ),
    )


@router.message(Command("savdo"))
async def cmd_savdo(message: Message):
    if not ADMIN_ID or str(message.from_user.id) != ADMIN_ID:
        await message.answer("❌ Sotish faqat admin uchun.")
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.answer(
            "🖼️ Mahsulot rasmini yuboring va shu rasmga *reply* qilib yozing:\n"
            "`/savdo <Nomi> <narx> <soni> <daraja>`\n\n"
            "Daraja:\n"
            "`1` -- Qotillik qurollari\n"
            "`2` -- Josus narsalari\n"
            "`3` -- Tozalash narsalar\n\n"
            "Misol:\n`/savdo ak47 2000 4 1`"
        )
        return
    parts = message.text.split()
    if len(parts) < 5:
        await message.answer(
            "Format to'g'ri emas!\n\n`/savdo <Nomi> <narx> <soni> <daraja>`\n\n"
            "Misol:\n`/savdo ak47 2000 4 1`"
        )
        return
    try:
        tier = int(parts[-1])
        stock = int(parts[-2])
        price = int(parts[-3])
        name = " ".join(parts[1:-3])
    except ValueError:
        await message.answer("Narx, soni va daraja son bo'lishi kerak!\n\nMisol:\n`/savdo ak47 2000 4 1`")
        return
    if tier not in TIER_NAMES:
        await message.answer(
            "Daraja 1, 2 yoki 3 bo'lishi kerak!\n\n"
            "`1` -- Qotillik qurollari\n`2` -- Josus narsalari\n`3` -- Tozalash narsalar"
        )
        return
    if price < 1:
        await message.answer("Narx 1 kreditdan kam bo'lmasin.")
        return
    if stock < 1:
        await message.answer("Soni 1 dan kam bo'lmasin.")
        return
    name = name.strip()
    photo_file_id = message.reply_to_message.photo[-1].file_id
    photo_url = ""
    try:
        file = await message.bot.get_file(photo_file_id)
        photo_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"
    except Exception:
        pass
    db.create_listing(message.from_user.id, name, price, photo_file_id, photo_url, stock, tier)
    tier_label, tier_name = TIER_NAMES[tier]
    await message.answer(
        f"✅ *{name}* qo'shildi!\n\n"
        f"💰 Narxi: {price} kredit\n"
        f"📦 Qoldiq: {stock} dona\n"
        f"{tier_label}: {tier_name}\n\n"
        "Endi u bot'dagi Do'kon darajasida va saytning 🧾 Vitrin bo'limida ko'rinadi. "
        "Har sotuvda kreditlar hisobingizga tushadi, soni kamayib boradi."
    )


@router.message(Command("unsell"))
async def cmd_unsell(message: Message):
    if not ADMIN_ID or str(message.from_user.id) != ADMIN_ID:
        await message.answer("❌ Sotish faqat admin uchun.")
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "🗑️ Sotuvni olib tashlash uchun:\n`/unsell <Mahsulot nomi> <narx>`\n\n"
            "Misol:\n`/unsell Qadimiy seyf 750`"
        )
        return
    try:
        price = int(parts[-1])
    except ValueError:
        await message.answer("Narx son bo'lishi kerak! Masalan: `/unsell Seyf 750`")
        return
    name = " ".join(parts[1:-1]).strip()
    removed = db.unsell_listing(name, price)
    if removed:
        await message.answer(
            f"🗑️ *{name}* ({price} kredit) vitrindan olib tashlandi.\n\n"
            f"O'chirilgan sotuvlar: {removed} ta"
        )
    else:
        await message.answer(f"[!] *{name}* ({price} kredit) bo'yicha faol sotuv topilmadi.")


@router.message(Command("kridit", "kredit"))
async def cmd_kridit(message: Message):
    if not ADMIN_ID or str(message.from_user.id) != ADMIN_ID:
        await message.answer("Siz admin emassiz.")
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer(
            "🎁 Kredit berish uchun:\n`/kridit <user_id> <kredit>`\n\n"
            "Misol:\n`/kridit 123456789 500`\n\n"
            "user_id -- foydalanuvchining Telegram ID si."
        )
        return
    try:
        user_id = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        await message.answer("[!] user_id va kredit son bo'lishi kerak.")
        return
    if amount < 1:
        await message.answer("[!] Kredit 1 dan kam bo'lmasin.")
        return
    user = db.get_user(user_id)
    if not user:
        await message.answer(f"[!] {user_id} topilmadi (bu foydalanuvchi bot'ga hali kirmagan).")
        return
    db.credit(user_id, amount)
    balance = db.get_user(user_id)["balance"]
    await message.answer(f"✅ {user_id} ga +{amount} kredit berildi.\n💰 Yangi balans: {balance}")
    try:
        await message.bot.send_message(
            user_id,
            f"🎁 Admin sizga +{amount} kredit berdi!\n💰 Balansingiz: {balance} kredit",
        )
    except Exception:
        pass


@router.message(Command("kod"))
async def cmd_kod(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "🎫 Kodni tekshirish uchun:\n`/kod <kod>`\n\n"
            "Misol:\n`/kod ghjagsyufuaasdf`"
        )
        return
    code = parts[1].strip().lower()
    row = db.get_code(code)
    if not row:
        await message.answer("[!] Bunday kod mavjud emas.")
        return
    await message.answer(
        f"✅ Kod mavjud!\n\n"
        f"🎨 {codes.info(row['color'])}\n"
        f"Kod: `{row['code']}`"
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not ADMIN_ID or str(message.from_user.id) != ADMIN_ID:
        await message.answer("Siz admin emassiz.")
        return
    users, codes_count, listings = db.stats()
    await message.answer(
        "👑 *ADMIN PANEL*\n\n"
        f"👥 Foydalanuvchilar: {users}\n"
        f"🎫 Yaratilgan kodlar: {codes_count}\n"
        f"🧾 Faol vitrin (sotuv): {listings}\n\n"
        "Kodlar web saytda yaratiladi va boshqariladi."
    )


@router.message(Command("kirish"))
async def cmd_kirish(message: Message):
    db.ensure_user(message.from_user.id, message.from_user.first_name, START_BALANCE)
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "🎫 Kod bilan kirish uchun:\n`/kirish <kod>`\n\n"
            "Misol:\n`/kirish ghjagsyufuaasdf`\n\n"
            "Kodlarni admin web sayt orqali yaratadi. Har bir kod faqat bir marta ishlatiladi."
        )
        return
    code = parts[1].strip().lower()
    row = db.use_code(code, message.from_user.id)
    if row is None:
        await message.answer("[!] Bunday kod topilmadi.\n\nKodlarni admin web saytda yaratadi. Kodingiz bo'lsa /kirish <kod> orqali kiring.")
        return
    if row is False:
        await message.answer(
            "⛔ *Bu kod allaqachon ishlatilgan!*\n\n"
            "Har bir kod faqat bitta foydalanuvchiga tegishli bo'lishi mumkin. "
            "Yangi kod uchun admin bilan bog'laning."
        )
        return
    db.set_code(message.from_user.id, row["color"])
    user = db.get_user(message.from_user.id)
    await message.answer(
        f"✅ Kod tasdiqlandi!\n\n{menu_text(user)}",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("mc"))
async def cmd_mc(message: Message):
    """Minecraft server o'yinchi nomini kodingizga bog'lash.

    Serverda qurollar avtomatik berilishi uchun:
      /kirish <kod>  ->  /mc <o'yinchi nomi>  ->  serverga kirish
    """
    db.ensure_user(message.from_user.id, message.from_user.first_name, START_BALANCE)
    code = db.get_code_by_user_id(message.from_user.id)
    if not code:
        await message.answer(
            "🎬 Avval kod bilan kiring:\n`/kirish <kod>`\n\n"
            "Kodni admin web saytda yaratadi."
        )
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "🎮 Minecraft o'yinchi nomingizni bog'lash uchun:\n"
            "`/mc <o'yinchi nomi>`\n\n"
            "Misol:\n`/mc Bayram7698`\n\n"
            "Shundan so'ng serverga kirganingizda sotib olgan qurollar avtomatik beriladi."
        )
        return
    nick = " ".join(parts[1:]).strip()
    if not nick or len(nick) > 16:
        await message.answer("[!] O'yinchi nomi 1-16 belgi bo'lishi kerak.")
        return
    status, info = db.bind_mc_nick(code, nick)
    if status == "notfound":
        await message.answer("[!] Kodingiz topilmadi. /kirish <kod> bilan qayta kiring.")
        return
    if status == "used":
        await message.answer(
            f"⛔ Bu kod boshqa o'yinchi nomiga bog'langan: `{info}`\n\n"
            "Yangi kod uchun admin bilan bog'laning."
        )
        return
    await message.answer(
        f"✅ Minecraft bog'landi!\n\n"
        f"🎮 O'yinchi: `{nick}`\n"
        f"🎫 Kod: `{code}`\n\n"
        f"Endi serverga kiring — qurollar avtomatik beriladi."
    )


def clan_help_text():
    return (
        "🛡️ *CLAN TIZIMI*\n\n"
        "Buyruqlar:\n"
        "`/clan yaratish <Nomi>` — clan yaratish\n"
        "`/clan tag <TAG>` — qisqa belgi o'rnatish (3-5 belgi)\n"
        "`/clan azo <ID yoki MC nick>` — a'zo qo'shish (faqat lider)\n"
        "`/clan chiqarish <ID yoki MC nick>` — a'zoni haydash (faqat lider)\n"
        "`/clan chiqish` — clandan chiqish\n"
        "`/clan tarqatish` — clan'ni tugatish (faqat lider)\n"
        "`/clan` — clan ma'lumoti va a'zolar ro'yxati\n\n"
        "Clan'ga qo'shish uchun o'yinchi avval `/mc <nick>` qilgan bo'lishi kerak."
    )


def clan_info_text(clan, members):
    tag = clan["tag"] or ""
    tag_txt = f" [{tag}]" if tag else ""
    lines = [f"🛡️ *CLAN: {clan['name']}{tag_txt}*\n"]
    for m in members:
        role = "👑 LIDER" if m["role"] == "owner" else "⚔️ A'ZO"
        name = m["name"] or f"ID:{m['user_id']}"
        mc = ""
        if m["code"]:
            user = db.get_user(m["user_id"])
            code = db.get_code_by_user_id(m["user_id"]) if user else None
            if code:
                row = db.get_code(code)
                mc = f" ({code})" if row else ""
        lines.append(f"{role} — {name}{mc}")
    return "\n".join(lines)


@router.message(Command("clan"))
async def cmd_clan(message: Message):
    db.ensure_user(message.from_user.id, message.from_user.first_name, START_BALANCE)
    parts = message.text.split(maxsplit=1)
    args = parts[1].strip() if len(parts) > 1 else ""
    arg_parts = args.split(maxsplit=1)
    action = arg_parts[0].lower() if arg_parts else ""
    rest = arg_parts[1].strip() if len(arg_parts) > 1 else ""

    if not action:
        clan = db.get_clan_by_user(message.from_user.id)
        if not clan:
            await message.answer(clan_help_text())
        else:
            members = db.get_clan_members(clan["id"])
            await message.answer(clan_info_text(clan, members))
        return

    if action == "yaratish":
        if not rest:
            await message.answer("[!] Clan nomi yozing:\n`/clan yaratish <Nomi>`")
            return
        if db.get_clan_by_user(message.from_user.id):
            await message.answer("⛔ Siz allaqachon biror clanda turibsiz. Avval chiqing.")
            return
        if db.get_clan_by_name(rest):
            await message.answer("⛔ Bunday nomli clan allaqachon mavjud.")
            return
        if len(rest) < 2 or len(rest) > 20:
            await message.answer("[!] Clan nomi 2-20 belgi bo'lishi kerak.")
            return
        clan_id = db.create_clan(rest, message.from_user.id)
        await message.answer(
            f"✅ *{rest}* clan yaratildi!\n\n"
            "Endi a'zo qo'shishingiz mumkin:\n`/clan azo <ID yoki MC nick>`\n\n"
            "Tag o'rnatish:\n`/clan tag <TAG>`"
        )
        return

    if action == "tag":
        clan = db.get_clan_by_user(message.from_user.id)
        if not clan:
            await message.answer("[!] Avval clan yarating: `/clan yaratish <Nomi>`")
            return
        if not db.is_clan_owner(clan["id"], message.from_user.id):
            await message.answer("⛔ Faqat lider tag o'rnata oladi.")
            return
        if not rest or not rest.isalnum() or len(rest) > 5:
            await message.answer("[!] TAG 1-5 belgi (harf/raqam) bo'lishi kerak.")
            return
        db.set_clan_tag(clan["id"], rest)
        await message.answer(f"✅ Clan tag'i o'rnatildi: `{rest}`")
        return

    if action == "azo":
        clan = db.get_clan_by_user(message.from_user.id)
        if not clan:
            await message.answer("[!] Avval clan yarating: `/clan yaratish <Nomi>`")
            return
        if not db.is_clan_owner(clan["id"], message.from_user.id):
            await message.answer("⛔ Faqat lider a'zo qo'sha oladi.")
            return
        if not rest:
            await message.answer("[!] A'zo ID'si yoki MC nick yozing:\n`/clan azo <ID yoki MC nick>`")
            return
        target_id = None
        if rest.isdigit():
            target_id = int(rest)
        else:
            target_id = db.get_user_id_by_mc_nick(rest)
            if not target_id:
                await message.answer(
                    f"[!] `{rest}` MC nick topilmadi. O'yinchi avval `/mc {rest}` qilishi kerak."
                )
                return
        if target_id == message.from_user.id:
            await message.answer("⛔ O'zingizni qo'sha olmaysiz, siz lider siz.")
            return
        user = db.get_user(target_id)
        if not user:
            await message.answer("[!] Bunday Telegram foydalanuvchi topilmadi.")
            return
        if db.get_clan_by_user(target_id):
            await message.answer("⛔ Bu o'yinchi boshqa clanda turibdi.")
            return
        db.add_clan_member(clan["id"], target_id)
        members = db.get_clan_members(clan["id"])
        await message.answer(
            f"✅ *{user['name']}* clan'ga qo'shildi!\n\n{clan_info_text(clan, members)}"
        )
        try:
            await message.bot.send_message(
                target_id,
                f"🛡️ Siz *{clan['name']}* clan'ga qo'shildingiz!\n\n"
                "Endi serverda qurollar clan belgisi bilan beriladi.",
            )
        except Exception:
            pass
        return

    if action == "chiqarish":
        clan = db.get_clan_by_user(message.from_user.id)
        if not clan:
            await message.answer("[!] Siz hech qanday clanda emassiz.")
            return
        if not db.is_clan_owner(clan["id"], message.from_user.id):
            await message.answer("⛔ Faqat lider a'zo chiqara oladi.")
            return
        if not rest:
            await message.answer("[!] A'zo ID'si yoki MC nick yozing:\n`/clan chiqarish <ID yoki MC nick>`")
            return
        target_id = None
        if rest.isdigit():
            target_id = int(rest)
        else:
            target_id = db.get_user_id_by_mc_nick(rest)
            if not target_id:
                await message.answer(f"[!] `{rest}` MC nick topilmadi.")
                return
        if target_id == message.from_user.id:
            await message.answer("⛔ Lider o'zini chiqara olmaydi. `/clan tarqatish` qiling.")
            return
        if not db.remove_clan_member(clan["id"], target_id):
            await message.answer("[!] Bu o'yinchi clan'da emas.")
            return
        await message.answer(f"🗑️ A'zo clan'dan chiqarildi!")
        try:
            await message.bot.send_message(
                target_id, f"🗑️ Siz *{clan['name']}* clan'dan chiqarildingiz."
            )
        except Exception:
            pass
        return

    if action == "chiqish":
        clan = db.get_clan_by_user(message.from_user.id)
        if not clan:
            await message.answer("[!] Siz hech qanday clanda emassiz.")
            return
        if db.is_clan_owner(clan["id"], message.from_user.id):
            await message.answer(
                "⛔ Siz lider siz. Clan'ni tugatish uchun:\n`/clan tarqatish`"
            )
            return
        db.remove_clan_member(clan["id"], message.from_user.id)
        await message.answer(f"✅ Siz *{clan['name']}* clan'dan chiqdingiz.")
        return

    if action == "tarqatish":
        clan = db.get_clan_by_user(message.from_user.id)
        if not clan:
            await message.answer("[!] Siz hech qanday clanda emassiz.")
            return
        if not db.is_clan_owner(clan["id"], message.from_user.id):
            await message.answer("⛔ Faqat lider clan'ni tugata oladi.")
            return
        db.delete_clan(clan["id"])
        await message.answer(f"🗑️ *{clan['name']}* clan tugatildi.")
        return

    await message.answer(clan_help_text())


@router.callback_query(F.data == "menu")
async def cb_menu(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    await cb.message.edit_text(menu_text(user), reply_markup=main_menu_keyboard())
    await cb.answer()


@router.callback_query(F.data.startswith("code:"))
async def cb_choose_code(cb: CallbackQuery):
    color = cb.data.split(":", 1)[1]
    db.set_code(cb.from_user.id, color)
    user = db.get_user(cb.from_user.id)
    await cb.message.edit_text(menu_text(user), reply_markup=main_menu_keyboard())
    await cb.answer("Kod tayinlandi! ✅")


@router.callback_query(F.data == "shop")
async def cb_shop(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    await cb.message.edit_text(
        "🏪 *DO'KON*\n\nQaysi bo'limga kiramiz?",
        reply_markup=shop_menu_keyboard(),
    )
    await cb.answer()


@router.callback_query(F.data == "catalog")
async def cb_catalog(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    for pid, item in products.CATALOG[user["code"]].items():
        await cb.bot.send_photo(
            cb.message.chat.id,
            URLInputFile(products.product_image(pid)),
            caption=(
                f"📦 *{item['name']}*\n"
                f"💰 Narxi: {item['price']} kredit\n"
                f"_{item['desc']}_"
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"🛒 Sotib olish — {item['price']} 💰",
                            callback_data=f"buy:cat:{pid}",
                        )
                    ]
                ]
            ),
        )
    await cb.message.edit_text(
        "📦 Katalog quyida yuborildi.",
        reply_markup=back_to_shop_keyboard(),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("tier:"))
async def cb_tier(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    try:
        tier = int(cb.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await cb.answer("Xatolik.", show_alert=True)
        return
    if tier not in TIER_NAMES:
        await cb.answer("Xatolik.", show_alert=True)
        return
    tier_label, tier_name = TIER_NAMES[tier]
    listings = [l for l in db.get_active_listings_by_tier(tier) if l["seller_id"] != cb.from_user.id]
    if not listings:
        await cb.message.edit_text(
            f"{tier_label} // *{tier_name}*\n\n"
            "Hozircha bo'sh.\n\n"
            "Sotuvchilar mahsulot qo'shishi bilanoq shu yerda ko'rinadi. "
            "O'zingiz ham sotishingiz mumkin: /savdo <Nomi> <narx> <soni> <daraja>",
            reply_markup=back_to_shop_keyboard(),
        )
        await cb.answer()
        return
    await cb.message.edit_text(f"{tier_label} // *{tier_name}*\n\nQuyida yuborildi.")
    for l in listings:
        await cb.bot.send_photo(
            cb.message.chat.id,
            l["photo_file_id"],
            caption=(
                f"🧾 *{l['name']}*\n"
                f"💰 Narxi: {l['price']} kredit\n"
                f"📦 Qoldiq: {l['stock']} dona\n"
                f"{tier_label}: {tier_name}"
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"📦 Buyurtma berish — {l['price']} 💰",
                            callback_data=f"buy:list:{l['id']}",
                        )
                    ]
                ]
            ),
        )
    await cb.message.answer(
        "⬅️ Do'konga qaytish",
        reply_markup=back_to_shop_keyboard(),
    )
    await cb.answer()


@router.callback_query(F.data == "vitrin")
async def cb_vitrin(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    listings = [l for l in db.get_active_listings() if l["seller_id"] != cb.from_user.id]
    if not listings:
        await cb.message.edit_text(
            "🧾 Vitrin hozircha bo'sh.\n\n"
            "O'z mahsulotingizni sotish uchun rasm yuborib, unga reply qiling:\n"
            "`/savdo <Nomi> <narx> <soni> <daraja>`",
            reply_markup=back_to_shop_keyboard(),
        )
        await cb.answer()
        return
    for l in listings:
        await cb.bot.send_photo(
            cb.message.chat.id,
            l["photo_file_id"],
            caption=(
                f"🧾 *{l['name']}*\n"
                f"💰 Narxi: {l['price']} kredit\n"
                f"📦 Qoldiq: {l['stock']} dona\n"
                f"_Sotuvchi: @{cb.bot.username}_"
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"📦 Buyurtma berish — {l['price']} 💰",
                            callback_data=f"buy:list:{l['id']}",
                        )
                    ]
                ]
            ),
        )
    await cb.message.edit_text(
        "🧾 Vitrin quyida yuborildi.",
        reply_markup=back_to_shop_keyboard(),
    )
    await cb.answer()


@router.callback_query(F.data == "sell_help")
async def cb_sell_help(cb: CallbackQuery):
    await cb.message.edit_text(
        "🛍️ *MAHSULOT SOTISH*\n\n"
        "1️⃣ Mahsulot rasmini yuboring\n"
        "2️⃣ Shu rasmga *reply* qilib yozing:\n"
        "`/savdo <Nomi> <narx> <soni> <daraja>`\n\n"
        "Daraja:\n"
        "`1` -- Qotillik qurollari\n"
        "`2` -- Josus narsalari\n"
        "`3` -- Tozalash narsalar\n\n"
        "Misol:\n`/savdo ak47 2000 4 1`\n\n"
        "Mahsulot bot'dagi Do'kon darajasida ko'rinadi. Har buyurtma "
        "tasdiqlanganda soni kamayadi, kreditlar hisobingizga tushadi!",
        reply_markup=back_to_shop_keyboard(),
    )
    await cb.answer()


@router.callback_query(F.data == "codes")
async def cb_codes(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    await cb.message.edit_text(
        codes.all_info(),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="menu")]]
        ),
    )
    await cb.answer()


@router.callback_query(F.data == "balance")
async def cb_balance(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    await cb.message.edit_text(
        f"💰 *Balansingiz:* {user['balance']} kredit",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="menu")]]
        ),
    )
    await cb.answer()


@router.callback_query(F.data == "inventory")
async def cb_inventory(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    items = db.get_inventory(cb.from_user.id)
    if not items:
        text = "🎒 *Inventaringiz bo'sh.*\n\nDo'kondan biror narsa xarid qiling!"
    else:
        lines = ["🎒 *Inventaringiz:*\n"]
        for pid, qty in items:
            if pid.startswith("listing:"):
                lid = int(pid.split(":", 1)[1])
                listing = db.get_listing(lid)
                name = listing["name"] if listing else "Mahsulot"
            else:
                _, item = products.find_product(pid)
                name = item["name"] if item else pid
            lines.append(f"▪️ {name} × {qty}")
        text = "\n".join(lines)
    await cb.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Asosiy menyu", callback_data="menu")]]
        ),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("buy:cat:"))
async def cb_buy_catalog(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    pid = cb.data.split(":", 2)[2]
    req_code, item = products.find_product(pid)
    if not item:
        await cb.answer("Mahsulot topilmadi.", show_alert=True)
        return
    if req_code != user["code"]:
        await cb.answer(
            f"Bu mahsulot faqat {products.CATEGORY_NAMES[req_code]} uchun!",
            show_alert=True,
        )
        return
    if user["balance"] < item["price"]:
        await cb.answer("Kreditingiz yetarli emas!", show_alert=True)
        return
    db.spend(cb.from_user.id, item["price"])
    db.add_item(cb.from_user.id, pid)
    balance = db.get_user(cb.from_user.id)["balance"]
    await cb.answer(
        f"✅ Sotib olindi: {item['name']}\nQolgan balans: {balance} 💰",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("buy:list:"))
async def cb_buy_listing(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    lid = int(cb.data.split(":", 2)[2])
    listing = db.get_listing(lid)
    if not listing or listing["status"] != "active":
        await cb.answer("Bu mahsulot allaqachon sotilgan!", show_alert=True)
        return
    if listing["seller_id"] == cb.from_user.id:
        await cb.answer("O'z mahsulotingizga buyurtma bera olmaysiz!", show_alert=True)
        return
    oid = db.create_order(
        user["code"],
        user["code"],
        cb.from_user.id,
        f"listing:{lid}",
        listing["name"],
        "🧾 Do'kon buyurtmasi",
        listing["price"],
        0,
    )
    try:
        await cb.bot.send_message(
            ADMIN_ID,
            f"[MURTHEHELP] YANGI BUYURTMA #{oid}\n"
            f"Mahsulot: {listing['name']}\n"
            f"Narx: {listing['price']} KREDIT\n"
            f"Xaridor: @{cb.from_user.username or cb.from_user.first_name}\n"
            f"Kod: {user['code']}\n"
            "Tasdiq: sayt admin paneli.",
        )
    except Exception:
        pass
    await cb.answer(
        f"✅ Buyurtma #{oid} adminga yuborildi!\n"
        "Admin tasdiqlagach mahsulot sotib olinadi, kredit hisobingizdan yechiladi.",
        show_alert=True,
    )


PENDING_MSG = {}


@router.callback_query(F.data == "write_admin")
async def cb_write_admin(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    PENDING_MSG[cb.from_user.id] = "admin"
    await cb.message.edit_text(
        "✍️ *ADMINGA YOZISH*\n\n"
        "Endi xabaringizni yozib yuboring. Admin tez orada javob beradi.",
        reply_markup=back_to_shop_keyboard(),
    )
    await cb.answer()


@router.callback_query(F.data == "order_request")
async def cb_order_request(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    PENDING_MSG[cb.from_user.id] = "order"
    await cb.message.edit_text(
        "📦 *BUYURTMA BERISH*\n\n"
        "Nima buyurtma qilmoqchisiz? Yozing.\n\n"
        "Misol:\n`ak47 2000 kreditga olmoqchiman`",
        reply_markup=back_to_shop_keyboard(),
    )
    await cb.answer()


@router.callback_query(F.data == "my_orders")
async def cb_my_orders(cb: CallbackQuery):
    user = await ensure_registered(cb)
    if not user:
        return
    orders = db.get_orders_by_code(user["code"])
    if not orders:
        text = "📦 *Buyurtmalaringiz bo'sh.*\n\nBuyurtma berish uchun do'konga kiring: /start"
    else:
        status_map = {"pending": "⏳ Kutilmoqda", "answered": "💬 Javob berildi", "sold": "✅ Sotildi"}
        lines = ["📦 *Buyurtmalaringiz:*\n"]
        for o in orders[:10]:
            lines.append(
                f"#{o['id']} {o['name']} -- {o['final_price'] or o['base_price']} KREDIT\n"
                f"  {status_map.get(o['status'], o['status'])}"
            )
        text = "\n".join(lines)
    await cb.message.edit_text(text, reply_markup=back_to_shop_keyboard())
    await cb.answer()


@router.message(F.text)
async def handle_user_text(message: Message):
    db.ensure_user(message.from_user.id, message.from_user.first_name, START_BALANCE)
    state = PENDING_MSG.pop(message.from_user.id, None)
    if state == "admin":
        try:
            await message.bot.send_message(
                ADMIN_ID,
                f"✍️ [XARIDOR → ADMIN]\n"
                f"@{message.from_user.username or message.from_user.first_name}\n"
                f"Telegram ID: {message.from_user.id}\n\n"
                f"{message.text}",
            )
        except Exception:
            pass
        await message.answer("✅ Xabaringiz adminga yuborildi!\n\nJavobini kuting.")
    elif state == "order":
        user = db.get_user(message.from_user.id)
        if not user or not user["code"]:
            await message.answer("Avval kod tanlang! /start bosing.")
            return
        oid = db.create_order(
            user["code"],
            user["code"],
            message.from_user.id,
            "custom",
            "📦 Maxsus buyurtma",
            message.text,
            0,
            0,
        )
        try:
            await message.bot.send_message(
                ADMIN_ID,
                f"[MURTHEHELP] YANGI BUYURTMA #{oid} (MAXSUS)\n"
                f"Xaridor: @{message.from_user.username or message.from_user.first_name}\n"
                f"Telegram ID: {message.from_user.id}\n"
                f"Kod: {user['code']}\n\n"
                f"So'rov: {message.text}",
            )
        except Exception:
            pass
        await message.answer(
            f"✅ Buyurtma #{oid} adminga yuborildi!\n\nAdmin javobini kuting."
        )
