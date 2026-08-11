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

3. Qurol addon'ini o'rnating. **Tanlangan: Absolute Guns 3 / M4 Update** (AzozGamer936)
   -- 23 qurol (AK-47, M4, M16, AK-74U, PKM, RPK, MG-42, RPG-7, MP5, UMP-45,
   M3/M1014/SPAS-12, Glock, flamethrower...). Script-based, dediker serverlarni
   qo'llab-quvvatlaydi.

   Fayl `mc-server/` papkasida allaqachon bor: `absolute-guns-3d.mcaddon`
   (licenziya "All Rights Reserved" -- git'ga commit QILINMAYDI).
   Yangi versiya: https://mcpedl.com/absolute-guns-3-3d/

   O'rnatish: `.mcaddon` faylini server yonidagi `worlds/<worldname>/behavior_packs/`
   papkasiga tashlang. World boshqa usulda ochilgan bo'lsa, `world_behavior_packs.json`
   ga qo'shing va world'ni qayta oching.

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

## weapons_map.json

Ushbu fayl Absolute Guns 3 uchun allaqachon to'ldirilgan -- bot'dagi mahsulot nomini
shu xaritadagi kalitlarga moslab qo'ying. Kalit = bot'dagi mahsulot nomi
(`/savdo` bilan yozilgan nom, katta-kichik ahamiyatsiz), qiymat = qurol ID si.

Amaldagi qurol ID lari (addon'dan olingan):

```
absolute_guns:ak47          absolute_guns:ak47_gold   absolute_guns:ak74u
absolute_guns:bizon         absolute_guns:flamethrower absolute_guns:glock
absolute_guns:glock_tactical absolute_guns:m1014      absolute_guns:m16
absolute_guns:m3            absolute_guns:m4          absolute_guns:mg42
absolute_guns:mgl           absolute_guns:mp40        absolute_guns:mp5
absolute_guns:mp5k          absolute_guns:pkm         absolute_guns:rpg7
absolute_guns:rpk           absolute_guns:spas        absolute_guns:tactical_knife
absolute_guns:tactical_knife_scope absolute_guns:ump45
```

Ammo: `pistol_ammo`, `rifle_ammo`, `smg_ammo`, `shotgun_ammo`, `sniper_ammo`,
`rpg7_ammo`, `machinegun_ammo` (hammasi `absolute_guns:` old qo'shimchasi bilan).

Masalan bot'da `/savdo AK-47 2000 4 1` deb mahsulot ochilsa, xaridor sotib olib
`/link <kod>` qilganda `absolute_guns:ak47` beriladi (xaritada "ak-47" kaliti bor).

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
