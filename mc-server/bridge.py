"""Qotillar Dokoni -- Minecraft Bedrock bridge.

BDS serveri logs/latest.log faylini kuzatadi va RCON orqali buyruqlar yuboradi:
  - o'yin chatida /link <kod> yoki !link <kod> kiritilsa:
      * kodni PA saytining /api/link endpointi bilan tekshiradi
      * muvaffaqiyatli bo'lsa allowlist'ga qo'shadi va sotib olingan qurollarni beradi
  - o'yinchi kirganda (Player Spawned) sotib olingan qurollarni qayta beradi
  - registratsiya qilingan o'yinchi ulansa (Player connected) avtomatik whitelist qiladi

Ishga tushirish:
    python bridge.py

Bridge server fayllari yonida (yoki bridge_config.json dagi server_dir da) ishlashi kerak.
"""

import json
import os
import re
import socket
import struct
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.path.join(HERE, "bridge_config.json")
    defaults = {
        "pa_url": "https://Sukuna9876.pythonanywhere.com",
        "bridge_key": "CHANGE_ME_LONG_RANDOM_BRIDGE_KEY",
        "rcon_host": "127.0.0.1",
        "rcon_port": 25575,
        "rcon_password": "changeme",
        "server_dir": ".",
        "weapons_map_file": "weapons_map.json",
        "allowlist_command": "allowlist add",
        "link_codes": ["/link", "!link"],
        "auto_whitelist": True,
        "give_on_spawn": True,
        "poll_delay": 1.0,
    }
    cfg = dict(defaults)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    return cfg


CFG = load_config()

RE_CONNECT = re.compile(r"Player connected: (.+?), xuid: (\d+)")
RE_SPAWN = re.compile(r"Player Spawned: (.+)")
RE_DISCONNECT = re.compile(r"Player disconnected: (.+)")
RE_CHAT = re.compile(r"Text of \[(.+?)\] ?: ?(.*)")


class Rcon:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.sock = None

    def _pack(self, rid, ptype, payload):
        body = struct.pack("<ii", rid, ptype) + payload.encode("utf-8") + b"\x00\x00"
        return struct.pack("<i", len(body)) + body

    def _read(self):
        s = self.sock
        head = s.recv(4)
        if len(head) < 4:
            raise RuntimeError("RCON ulanish yopildi")
        (length,) = struct.unpack("<i", head)
        data = b""
        while len(data) < length:
            chunk = s.recv(length - len(data))
            if not chunk:
                break
            data += chunk
        rid, ptype, payload = struct.unpack("<ii", data[:8])
        return payload[:-2].decode("utf-8", "replace")

    def connect(self):
        s = socket.create_connection((self.host, self.port), timeout=5)
        s.settimeout(5)
        s.send(self._pack(1, 3, self.password))
        resp = s.recv(4)
        if len(resp) < 4:
            raise RuntimeError("RCON javob bermadi")
        (length,) = struct.unpack("<i", resp)
        data = b""
        while len(data) < length:
            data += s.recv(length - len(data))
        rid, ptype = struct.unpack("<ii", data[:8])
        s.close()
        if rid == -1:
            raise RuntimeError("RCON parol noto'g'ri")
        self.sock = socket.create_connection((self.host, self.port), timeout=5)
        self.sock.settimeout(5)
        return True

    def command(self, cmd):
        if not self.sock:
            self.connect()
        try:
            self.sock.send(self._pack(2, 2, cmd))
            return self._read()
        except Exception:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
            self.connect()
            self.sock.send(self._pack(2, 2, cmd))
            return self._read()

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


class Tailer:
    def __init__(self, path):
        self.path = path
        self.pos = 0

    def readlines(self):
        try:
            size = os.path.getsize(self.path)
            if size < self.pos:
                self.pos = 0
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self.pos)
                lines = f.readlines()
                self.pos = f.tell()
            return lines
        except OSError:
            return []


def api(path, params=None, payload=None):
    url = CFG["pa_url"].rstrip("/") + path
    headers = {"X-Bridge-Key": CFG["bridge_key"]}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    elif params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def rawtext(text):
    return json.dumps({"rawtext": [{"text": text}]})


def load_weapons_map():
    path = os.path.join(HERE, CFG["weapons_map_file"])
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {str(k).lower(): v for k, v in data.get("weapons", data).items()}
    except OSError:
        return {}


def lookup(wmap, name, key):
    for k in (name, key):
        if not k:
            continue
        v = wmap.get(k.lower()) or wmap.get(k)
        if v:
            return v
    return None


def give_all(rcon, nick, weapons, wmap, given, force=False):
    bucket = given.setdefault(nick, {})
    for w in weapons or []:
        item = lookup(wmap, w.get("name") or "", w.get("key") or "")
        if not item:
            log("MAPPING YO'Q: '{}' -> weapons_map.json ga qurol ID qo'shing".format(w.get("name")))
            continue
        qty = int(w.get("qty") or 1)
        if not force and bucket.get(item, 0) >= qty:
            continue
        rcon.command('give "{}" {} {}'.format(nick, item, qty))
        bucket[item] = qty
        log("GIVE: {} <- {} x{}".format(nick, item, qty))


def handle_link(nick, code, rcon, wmap, given):
    try:
        res = api("/api/link", payload={"code": code, "nick": nick})
    except Exception as e:
        log("API /api/link xato: " + str(e))
        rcon.command("tellraw @a " + rawtext("ROBOT: serverga bog'lanishda xato, keyinroq urinib ko'ring."))
        return
    if not res.get("ok"):
        err = res.get("error")
        msg = "ROBOT: kod topilmadi. /link <kod> qayta urinib ko'ring."
        if err == "used":
            msg = "ROBOT: bu kod boshqa nickga bog'langan ({}).".format(res.get("nick"))
        elif err == "bad_input":
            msg = "ROBOT: kod yoki nick noto'g'ri."
        rcon.command("tellraw @a " + rawtext(msg))
        return
    if CFG["auto_whitelist"]:
        rcon.command("{} {}".format(CFG["allowlist_command"], nick))
    give_all(rcon, nick, res.get("weapons", []), wmap, given, force=True)
    rcon.command("tellraw @a " + rawtext("ROBOT: {} muvaffaqiyatli ulandi! Qurollaringiz berildi.".format(nick)))


def handle_line(line, rcon, wmap, given):
    line = line.strip()

    m = RE_CONNECT.search(line)
    if m:
        nick, xuid = m.group(1).strip(), m.group(2)
        if CFG["auto_whitelist"]:
            try:
                api("/api/weapons", {"nick": nick})
                rcon.command("{} {}".format(CFG["allowlist_command"], nick))
                log("AVTO WHITELIST: {} (xuid {})".format(nick, xuid))
            except Exception:
                pass
        return

    m = RE_SPAWN.search(line)
    if m:
        nick = m.group(1).strip()
        if CFG["give_on_spawn"]:
            try:
                res = api("/api/weapons", {"nick": nick})
                if res.get("ok"):
                    give_all(rcon, nick, res.get("weapons", []), wmap, given)
            except Exception as e:
                log("spawn qurollari xatosi: " + str(e))
        return

    m = RE_DISCONNECT.search(line)
    if m:
        nick = m.group(1).strip()
        given.pop(nick, None)
        return

    m = RE_CHAT.search(line)
    if m:
        nick, msg = m.group(1).strip(), m.group(2).strip()
        first, sep, rest = msg.partition(" ")
        if sep and first.lower() in CFG["link_codes"]:
            handle_link(nick, rest.strip().lower(), rcon, wmap, given)


def log(msg):
    print("[{}] {}".format(time.strftime("%H:%M:%S"), msg), flush=True)


def main():
    log_path = os.path.join(CFG["server_dir"], "logs", "latest.log")
    rcon = Rcon(CFG["rcon_host"], CFG["rcon_port"], CFG["rcon_password"])
    wmap = load_weapons_map()
    tailer = Tailer(log_path)
    given = {}

    log("Bridge ishga tushdi. PA: {}".format(CFG["pa_url"]))
    log("Qurol xaritasi: {} ta element".format(len(wmap)))

    while True:
        try:
            rcon.command("list")
        except Exception:
            log("RCON mavjud emas, 5 soniyadan keyin qayta tekshiriladi...")
            time.sleep(5)
            continue
        for line in tailer.readlines():
            try:
                handle_line(line, rcon, wmap, given)
            except Exception as e:
                log("satr ishlovida xato: " + str(e))
        time.sleep(CFG["poll_delay"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBridge to'xtatildi.")
