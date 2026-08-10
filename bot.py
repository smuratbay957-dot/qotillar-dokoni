import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import db
import handlers
from config import BOT_TOKEN


async def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN topilmadi! .env faylini yarating yoki muhit o'zgaruvchisini o'rnating."
        )
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()
    dp.include_router(handlers.router)
    db.init_db()
    me = await bot.get_me()
    await bot.delete_webhook(drop_pending_updates=True)
    print(f"* QOTILLAR DO'KONI bot ishga tushdi: @{me.username}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
