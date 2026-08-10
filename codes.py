CODES = {
    "red": {
        "emoji": "🔴",
        "title": "Qizil kod — Qotil",
        "desc": (
            "Murthehelp do'konining asosiy mijozlari. Ular qurol-yarog', "
            "bomba, zahar kabi o'ldirish uchun kerakli narsalarni xarid qilishadi."
        ),
    },
    "purple": {
        "emoji": "🟣",
        "title": "Binafsha kod — Josus",
        "desc": (
            "Axborotni sotuvchi va xaridorlar. Tinglash qurilmalari, "
            "maxfiy kameralar, shifrlangan aloqa vositalaridan foydalanishadi."
        ),
    },
    "yellow": {
        "emoji": "🟡",
        "title": "Sariq kod — Tozalovchi",
        "desc": (
            "Ishdan keyingi izlarni yo'qotuvchilar. Tozalash vositalari, "
            "dori-darmon, hujjat soxtalashtirish va qonundan qochishga "
            "yordam beradigan xizmatlardan foydalanishadi."
        ),
    },
    "green": {
        "emoji": "🟢",
        "title": "Yashil kod — Himoyalangan",
        "desc": (
            "Bu toifa emas, balki maxsus himoyalangan shaxslar — kino'dagi "
            "Jin-man va Ji-an kabi. Kod egalari ularga hech qachon hujum "
            "qilmaydi; kim bu qoidani buzsа, hamma kod egalari ularni "
            "hayotini xavf ostiga qo'yib himoya qilishga majbur."
        ),
    },
}


def info(code):
    c = CODES[code]
    return f"{c['emoji']} {c['title']}"


def all_info():
    lines = [
        "🎨 *KODLAR HAQIDA* (kino'dagidek)\n",
    ]
    for c in CODES.values():
        lines.append(f"{c['emoji']} *{c['title']}*\n{c['desc']}\n")
    lines.append(
        "⚠️ *Eslatma:* bularning barchasi 'A Shop for Killers' kinosi asosidagi "
        "soxta o'yin. Haqiqatda hech qanday zo'ravonlik yo'q, faqat ko'ngil "
        "ochish uchun! 😄"
    )
    return "\n".join(lines)
