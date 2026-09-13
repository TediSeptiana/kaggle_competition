"""dump_obs.py
Jalankan: python dump_obs.py

Output:
  - obs_dump/step_XXXX.json   (1 file per step)
  - obs_dump/summary.txt      (ringkasan human-readable)
  - obs_dump/latest.json      (obs terakhir, untuk inspect manual)
"""

import json
import os
from kaggle_environments import make

# Import agent (sesuaikan kalau namamu beda)
from main import agent as my_agent


OUT_DIR = "obs_dump"
MAX_STEPS_DUMP = 720        # batasi kalau cuma mau beberapa step pertama


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def safe_json(obj):
    """Best-effort serialize numpy/float/int/tuple."""
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return str(obj)


def main():
    ensure_dir(OUT_DIR)
    env = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)

    # Simpan trace per step
    print(f"Running env... output ke ./{OUT_DIR}/")
    env.run([my_agent, "random"])

    with open(os.path.join(OUT_DIR, "summary.txt"), "w", encoding="utf-8") as fsummary:
        for t, states in enumerate(env.steps[:MAX_STEPS_DUMP]):
            if not isinstance(states, list) or not states:
                continue

            # Simpan untuk PLAYER 0 saja (bot kita)
            s = states[0]
            obs = s.get("observation") if isinstance(s, dict) else None
            if not obs:
                continue

            # 1) Simpan full obs
            path = os.path.join(OUT_DIR, f"step_{t:04d}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(safe_json(obs), f, indent=2)

            # 2) Simpan obs terakhir untuk inspect cepat
            if t == len(env.steps) - 1 or t == MAX_STEPS_DUMP - 1:
                with open(os.path.join(OUT_DIR, "latest.json"),
                          "w", encoding="utf-8") as f:
                    json.dump(safe_json(obs), f, indent=2)

            # 3) Ringkasan human-readable
            fsummary.write(format_summary(t, s, obs))
            fsummary.write("\n")

    print(f"✅ Selesai. Cek folder ./{OUT_DIR}/")
    print(f"   File per step : step_0000.json, step_0001.json, ...")
    print(f"   File terakhir : latest.json")
    print(f"   Ringkasan     : summary.txt")


def format_summary(t, state, obs):
    """Ringkasan 1 step dalam bahasa manusia."""
    out = []
    out.append("=" * 72)
    out.append(f"STEP {t} | day={obs['day']} hour={obs['hour']} player={obs['player']}")
    out.append("=" * 72)

    # Action yang dijalankan turn sebelumnya
    action = state.get("action") if isinstance(state, dict) else None
    out.append(f"action    : {action}")
    out.append(f"reward    : {state.get('reward')}  status: {state.get('status')}")

    # Farm kita
    me = obs["farms"][obs["player"]]
    out.append("")
    out.append("--- FARM (kita) ---")
    out.append(f"  money      : {me['money']:.0f}")
    out.append(f"  farmer     : {me['farmer']}")
    out.append(f"  hands      : {me['hands']}")
    out.append(f"  unlocked   : {me['unlocked_quadrants']}")
    out.append(f"  hires_today: {me['hires_today']}")

    # Tiles — hanya tampilkan yang BUKAN None / LOCKED
    out.append("")
    out.append("  Tiles yang berisi objek:")
    any_tile = False
    for y, row in enumerate(me["tiles"]):
        for x, tile in enumerate(row):
            if tile is None:
                continue
            if tile == "LOCKED":
                continue
            any_tile = True
            out.append(f"    ({x},{y}) : {tile}")
    if not any_tile:
        out.append("    (kosong — semua tile None atau LOCKED)")

    # Private state
    priv = obs.get("private", {})
    out.append("")
    out.append("--- PRIVATE ---")
    out.append(f"  shed       : {priv.get('shed', {})}")
    out.append(f"  seeds      : {priv.get('seeds', {})}")
    out.append(f"  inventories: {priv.get('inventories', [])}")

    # Market
    market = obs.get("market", {})
    out.append("")
    out.append("--- MARKET ---")
    out.append(f"  prices    : {market.get('prices', {})}")
    out.append(f"  inventory : {market.get('inventory', {})}")

    # Town
    town = obs.get("town", {})
    out.append("")
    out.append("--- TOWN ---")
    out.append(f"  unlocked_shops: {town.get('unlocked_shops', [])}")

    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    main()