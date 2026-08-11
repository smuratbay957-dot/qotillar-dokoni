# Qotillar Dokoni -- Minecraft Bedrock server

Bot orqali sotib olingan qurollar RP (roleplay) serverida beriladi.
Ushbu papka BDS (rasmiy Bedrock Dedicated Server) yonida turadi va quyidagilarni qiladi:

- `bridge.py` -- BDS `logs/latest.log` jurnalini kuzatadi, chatda `/link <kod>` ni ushlaydi,
  PythonAnywhere'dagi sayt API'si orqali koddni tekshiradi, allowlist'ga qo'shadi va
  sotib olingan qurollarni `/give` bilan beradi.
- `bridge_config.json` -- sozlamalar (PA manzili, BRIDGE_KEY, RCON, ...).
- `weapons_map.json` -- bot'dagi mahsulot nomi -> o'yindagi qurol ID si.

## Bir martalik sozlash (BDS)

1. BDS ni yuklab oling: https://www.minecraft.net/en-us/download/server/bedrock
   (Windows yoki Linux versiyasi). Zip'ni papkaga oching (masalan `C:\mc-server\`).

2. `server.properties` ni oching va quyidagilarni o'rnating (namuna:
   `server.properties.example`):

   ```
   allow-cheats=true
   enable-rcon=true
   rcon-port=25575
   rcon-password=changeme
   ```

   `allow-list` ni `false` qoldiring -- bridge `/link` qilgan o'yinchilarni o'zi qo'shadi
   va registratsiya qilingan o'yinchini ulanganda avtomatik whitelist qiladi.
   (Istalgan vaqtda `allow-list=true` qilishingiz mumkin.)

3. Qurol addon'ini o'rnating: tanlagan addon'ingiz behavior pack'ini server yonidagi
   `worlds/<worldname>/behavior_packs/` papkasiga tashlang va world'ni oching.

4. `mc-server/` papkasidagi fayllarni BDS papkasiga ko'chiring (yoki `server_dir` ni
   o'zgartiring).

5. Sozlamalar faylini yarating:
   ```
   copy bridge_config.json.example bridge_config.json
   ```
   (bu fayl `.gitignore` da -- maxfiy kalit bo'lgani uchun commit qilinmaydi)

## Sozlash: bridge_config.json

```json
{
  "pa_url": "https://Sukuna9876.pythonanywhere.com",
  "bridge_key": "CHANGE_ME_LONG_RANDOM_BRIDGE_KEY",
  "rcon_host": "127.0.0.1",
  "rcon_port": 25575,
  "rcon_password": "changeme",
  "server_dir": ".",
  "allowlist_command": "allowlist add",
  "link_codes": ["/link", "!link"],
  "auto_whitelist": true,
  "give_on_spawn": true
}
```

- `bridge_key` -- PA'da `.env` dagi `BRIDGE_KEY` bilan bir xil bo'lishi shart.
- `rcon_port` / `rcon_password` -- `server.properties` dagi bilan bir xil.
- `pa_url` -- sizning PythonAnywhere manzilingiz.
- `server_dir` -- BDS fayllari turgan papka (`.` = shu papka).
- `link_codes` -- o'yin chatida ishlaydigan buyruqlar. O'yinchi:
  ```
  /link <kod>
  ```
  yozadi (kod bot'dagi /kirish kodi bilan bir xil).

## Sozlash: weapons_map.json

Kalit = bot'dagi mahsulot nomi (`/savdo` bilan yozilgan nom, katta-kichik ahamiyatsiz).
Qiymat = o'yindagi qurol ID si (addon'ning `identifier` maydoni).

Addon ID'sini qanday topish: addon papkasini oching, `items/` da `.item.json` fayllar
bor. Har bir faylda `"identifier": "namespace:name"` qatori bo'ladi -- shuni qiymatga
yozing. Masalan "Absolute Guns 3D" addonida:

```json
{
  "weapons": {
    "ak47": "absolute_guns:ak47",
    "m4a1": "absolute_guns:m4a1"
  }
}
```

O'yinchi qurol sotib olib `/link <kod>` qilganda, qurol nomi shu xaritada topilsa
`give` buyrug'i yuboriladi. Topilmasa bridge konsolida "MAPPING YO'Q" chiqadi.

## Ishga tushirish

1. Avval BDS serverini ishga tushiring (`bedrock_server.exe` / `./bedrock_server`).
2. Keyin bridge'ni ishga tushiring:
   ```
   python bridge.py
   ```
   (Windows'da `py bridge.py`). Bridge server bilan birga doim ishlab turishi kerak.
   Doimiy qilish uchun: Windows'da "Task Scheduler", Linux'da `systemd` yoki `screen`.

## Ishlash tartibi

1. Xaridor bot'da kod oladi va `/kirish <kod>` qiladi (kod Telegram hisobiga bog'lanadi).
2. Do'kondan qurol sotib oladi.
3. Serverga kiradi, chatga `/link <kod>` yozadi.
4. Bridge kodni tekshiradi, o'yinchini allowlist'ga qo'shadi va qurollarni beradi.
5. Keyingi safar serverga kirganda qurollar avtomatik qayta beriladi
   (faqat `/link` qilgan nick uchun, `give_on_spawn` = true bo'lsa).

## API (PythonAnywhere sayti)

- `POST /api/link` -- JSON `{code, nick}`, header `X-Bridge-Key: <key>`
  -> `{ok:true, weapons:[{key,name,qty}]}`
- `GET /api/weapons?nick=<nick>` -- o'yinchi kirganda qurollarni qaytaradi.

Bu endpointlar bridge tomonidan chaqiriladi; `BRIDGE_KEY` `.env` da bo'lmasa ishlamaydi.
