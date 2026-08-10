CATALOG = {
    "red": {
        "red_knife": {"name": "Jangovar pichoq", "price": 250, "desc": "Zarbdor, ovozsiz va halokatli."},
        "red_gun": {"name": "To'pponcha", "price": 600, "desc": "Kompakt, tez va aniq."},
        "red_poison": {"name": "Yashirin zahar", "price": 400, "desc": "Iz qoldirmaydigan modda."},
        "red_bomb": {"name": "Portlovchi paket", "price": 800, "desc": "Masofadan boshqariladi."},
        "red_vest": {"name": "Kevlar jilet", "price": 500, "desc": "O'q o'tkazmaydigan himoya."},
    },
    "purple": {
        "purple_bug": {"name": "Quloq solish moslamasi", "price": 300, "desc": "Hamma narsani eshitadi."},
        "purple_cam": {"name": "Yashirin kamera", "price": 350, "desc": "Ko'zga ko'rinmas nazorat."},
        "purple_gps": {"name": "GPS kuzatuvchi", "price": 250, "desc": "Har bir qadamni kuzatadi."},
        "purple_radio": {"name": "Shifrlangan aloqa", "price": 450, "desc": "Tinglab bo'lmaydigan kanal."},
    },
    "yellow": {
        "yellow_kit": {"name": "Tozalash to'plami", "price": 200, "desc": "Hech qanday iz qoldirmaydi."},
        "yellow_cleaner": {"name": "Neutralizator", "price": 350, "desc": "Qiyin joylarni ham tozalaydi."},
        "yellow_det": {"name": "Iz detektori", "price": 400, "desc": "Qolgan izlarni topadi."},
        "yellow_docs": {"name": "Soxta hujjatlar", "price": 500, "desc": "Yangi shaxs, yangi hayot."},
    },
    "green": {
        "green_safe": {"name": "Himoya kapsulasi", "price": 600, "desc": "Hujumdan to'liq himoya."},
        "green_car": {"name": "Qochish avtomobili", "price": 900, "desc": "Eng xavfli vaziyatda ham uchib ketadi."},
        "green_med": {"name": "Tibbiy to'plam", "price": 300, "desc": "Jarohatni joyida davolaydi."},
        "green_mask": {"name": "Tanib bo'lmas niqob", "price": 250, "desc": "Sizni hech kim tanimaydi."},
    },
}

CATEGORY_NAMES = {
    "red": "🔴 Qizil kod bo'limi (Qotillar)",
    "purple": "🟣 Binafsha kod bo'limi (Josuslar)",
    "yellow": "🟡 Sariq kod bo'limi (Tozalovchilar)",
    "green": "🟢 Yashil kod bo'limi (Himoyalanganlar)",
}


def find_product(pid):
    for code, items in CATALOG.items():
        if pid in items:
            return code, items[pid]
    return None, None


def product_image(pid):
    return f"https://picsum.photos/seed/{pid}/600/400"
