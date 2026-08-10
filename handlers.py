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
            [InlineKeyboardButton(text="📦 Katalog (mening kodim)", callback_data="catalog")],
            [InlineKeyboardButton(text="🧾 Vitrin (boshqa sotuvchilar)", callback_data="vitrin")],
            [InlineKeyboardButton(text="🛍️ Mahsulot sotish", callback_data="sell_help")],
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
    db.ensure_user(message.from_user.id, message.from_user.first_name, START_BALANCE)
    user = db.get_user(message.from_user.id)
    if not user or not user["code"]:
        await message.answer("Avval /kirish <kod> orqali kiring!")
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.answer(
            "🖼️ Mahsulot rasmini yuboring va shu rasmga *reply* qilib yozing:\n"
            "`/savdo Mahsulot nomi narxi`\n\n"
            "Misol:\n`/savdo Qadimiy seyf 750`"
        )
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Format noto'g'ri!\n\n`/savdo Mahsulot nomi narxi`")
        return
    try:
        price = int(parts[-1])
    except ValueError:
        await message.answer("Narx son bo'lishi kerak! Masalan: `/savdo Seyf 750`")
        return
    if price < 1:
        await message.answer("Narx 1 kreditdan kam bo'lmasin.")
        return
    name = " ".join(parts[1:-1])
    photo_file_id = message.reply_to_message.photo[-1].file_id
    db.create_listing(message.from_user.id, name, price, photo_file_id)
    await message.answer(
        f"✅ *{name}* vitringa qo'shildi!\n\n"
        f"💰 Narxi: {price} kredit\n"
        "Endi u 🧾 Vitrin bo'limida boshqa foydalanuvchilarga ko'rinadi. "
        "Sotilganda pul hisobingizga tushadi."
    )


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
            "Kodlarni admin web sayt orqali yaratadi."
        )
        return
    code = parts[1].strip().lower()
    row = db.get_code(code)
    if not row:
        await message.answer("[!] Bunday kod topilmadi.\n\nKodlarni admin web saytda yaratadi. Kodingiz bo'lsa /kirish <kod> orqali kiring.")
        return
    db.set_code(message.from_user.id, row["color"])
    user = db.get_user(message.from_user.id)
    await message.answer(
        f"✅ Kod tasdiqlandi!\n\n{menu_text(user)}",
        reply_markup=main_menu_keyboard(),
    )


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
            "`/savdo Mahsulot nomi narxi`",
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
                f"_Sotuvchi: @{cb.bot.username}_"
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"🛒 Sotib olish — {l['price']} 💰",
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
        "`/savdo Mahsulot nomi narxi`\n\n"
        "Misol:\n`/savdo Qadimiy seyf 750`\n\n"
        "Mahsulot 🧾 Vitrinda ko'rinadi, boshqalar sotib olishi mumkin. "
        "Sotilganda kreditlar hisobingizga tushadi!",
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
        await cb.answer("O'z mahsulotingizni sotib ololmaysiz!", show_alert=True)
        return
    if user["balance"] < listing["price"]:
        await cb.answer("Kreditingiz yetarli emas!", show_alert=True)
        return
    db.spend(cb.from_user.id, listing["price"])
    db.add_item(cb.from_user.id, f"listing:{lid}")
    db.credit(listing["seller_id"], listing["price"])
    db.close_listing(lid, cb.from_user.id)
    await cb.answer("✅ Xarid muvaffaqiyatli!", show_alert=True)
    try:
        await cb.bot.send_message(
            listing["seller_id"],
            f"🎉 Sizning *{listing['name']}* mahsulotingiz sotildi!\n"
            f"Hisobingizga +{listing['price']} kredit tushdi.",
        )
    except Exception:
        pass
