"""
visualize_sequence.py
Jalankan: python visualize_sequence.py
Output:
 - animasi pergerakan farmer di grid farm (matplotlib)
 - tabel trace posisi + action tiap turn
 - cek otomatis apakah obs punya key 'step' & apakah tile-nya LOCKED
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, Rectangle
from kaggle_environments import make

# --- Import agent-mu (sesuaikan path/nama) ---
import importlib.util

spec = importlib.util.spec_from_file_location("seq_agent", "main.py")
mod  = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

# main.py mendefinisikan `agent`, bukan `sequence_agent`
sequence_agent = getattr(mod, "sequence_agent", None) or mod.agent

CROP_COLORS = {
    "WHEAT":"#e8d96a","CARROT":"#f4a261","TOMATO":"#e63946",
    "STRAWBERRY":"#ff6b9d","MELON":"#90be6d",
}
def tile_color(t):
    if t == "LOCKED":       return "#333333"
    if t is None:           return "#f0ead6"
    if isinstance(t, dict):
        k = t.get("kind")
        if k == "PLANT":    return CROP_COLORS.get(t.get("crop"), "#6ab04c")
        if k == "WEED":     return "#8b6f47"
        if k == "COOP":     return "#ff8a65" if t.get("animal") else "#ffcc80"
        if k == "PASTURE":  return "#7cb342" if t.get("animal") else "#c5e1a5"
    return "#cccccc"

def tile_label(t):
    if t is None:           return ""
    if t == "LOCKED":       return "LOCK"
    if isinstance(t, dict):
        k = t.get("kind")
        if k == "PLANT":    return (t.get("crop") or "?")[:3]
        if k == "WEED":     return "WEED"
        if k == "COOP":     return "COOP" if not t.get("animal") else "GOOSE"
        if k == "PASTURE":  return "PAST"
    return ""

def hex_rgb(h):
    h = h.lstrip("#"); return [int(h[i:i+2],16)/255 for i in (0,2,4)]

def extract_frames(env, player=0):
    frames = []
    for t, states in enumerate(env.steps):
        if not isinstance(states, list) or len(states) <= player: continue
        s = states[player]
        obs = s.get("observation") if isinstance(s, dict) else None
        if not obs or "farms" not in obs: continue
        me = obs["farms"][obs["player"]]
        frames.append({
            "t": t,
            "day": obs["day"], "hour": obs["hour"],
            "step_calc": obs["day"]*24 + obs["hour"],
            "has_step_key": "step" in obs,
            "tiles": [row[:] for row in me["tiles"]],
            "farmer": tuple(me["farmer"]),
            "hands":  [tuple(h) for h in me["hands"]],
            "money":  me["money"],
            "unlocked": me["unlocked_quadrants"],
            "action": s.get("action"),
        })
    return frames

def visualize(frames, save_gif=None):
    H = len(frames[0]["tiles"]); W = len(frames[0]["tiles"][0])
    fig, ax = plt.subplots(figsize=(7, 7.5))

    def render(i):
        f = frames[i]; ax.clear()
        ax.set_xlim(-0.5, W-0.5); ax.set_ylim(H-0.5, -0.5)
        ax.set_aspect("equal")

        for y in range(H):
            for x in range(W):
                tile = f["tiles"][y][x]
                ax.add_patch(Rectangle((x-0.5,y-0.5),1,1,
                             facecolor=hex_rgb(tile_color(tile)),
                             edgecolor="gray", lw=0.3))
                lbl = tile_label(tile)
                if lbl:
                    ax.text(x, y, lbl, ha="center", va="center",
                            fontsize=6, color="black", alpha=0.7)

        # Shed area (tengah board)
        cx, cy = W/2-0.5, H/2-0.5
        ax.add_patch(Rectangle((cx-1,cy-1),2,2, fill=False,
                     edgecolor="black", lw=1.5, ls="--", zorder=2))
        ax.text(cx, cy-1.05, "SHED", ha="center", fontsize=7, zorder=3)

        # Farmer + hands
        fx, fy = f["farmer"]
        ax.add_patch(Circle((fx,fy),0.35, facecolor="#d32f2f",
                     edgecolor="white", lw=1.2, zorder=5))
        ax.text(fx, fy, "F", ha="center", va="center",
                color="white", weight="bold", zorder=6)
        for hx, hy in f["hands"]:
            ax.add_patch(Circle((hx,hy),0.25, facecolor="#1976d2",
                         edgecolor="white", lw=1, zorder=5))

        ax.set_xticks(range(W)); ax.set_yticks(range(H))
        ax.tick_params(labelsize=6)
        ax.set_title(
            f"t={f['t']}  day={f['day']} hour={f['hour']}  "
            f"(calc step={f['step_calc']})\n"
            f"farmer=({fx},{fy})  hands={f['hands']}  "
            f"money=${f['money']:.0f}  unlocked={f['unlocked']}\n"
            f"action={f['action']}", fontsize=8)
        return []

    anim = animation.FuncAnimation(fig, render, frames=len(frames),
                                   interval=300, blit=False, repeat=False)
    if save_gif:
        anim.save(save_gif, writer="pillow", fps=4)
        print(f"GIF tersimpan: {save_gif}")
    plt.tight_layout(); plt.show()
    return anim
if __name__ == "__main__":
    import os, sys, webbrowser
    from matplotlib import rcParams
    rcParams["animation.embed_limit"] = 100  # kalau mau HTML embed

    env = make("kaggriculture", debug=True)
    env.run([sequence_agent, "random"])

    frames = extract_frames(env)
    print(f"Total frame: {len(frames)}")
    print(f"obs punya key 'step'? -> {frames[0]['has_step_key']}")
    if not frames[0]["has_step_key"]:
        print("!! obs TIDAK punya key 'step'. Agent kamu pakai obs.get('step',0) "
              "-> selalu dianggap step 0, farmer tidak akan bergerak !!")

    print("\n== TRACE 30 turn pertama ==")
    print(f"{'t':>4} {'day':>4} {'hr':>3} {'step_calc':>9} {'farmer':>10} "
          f"{'unlocked':>20}  action")
    for f in frames[:30]:
        act  = f["action"]
        act_s = act.get("farmer") if isinstance(act, dict) else act
        mk    = act.get("market") if isinstance(act, dict) else None
        print(f"{f['t']:>4} {f['day']:>4} {f['hour']:>3} {f['step_calc']:>9} "
              f"{str(f['farmer']):>10} {str(f['unlocked']):>20}  "
              f"farmer={act_s}  market={mk}")

    # --- 1. Simpan GIF secara eksplisit ---
    gif_path = os.path.abspath("sequence_agent.gif")
    anim = visualize(frames)                # TANPA plt.show dulu
    try:
        anim.save(gif_path, writer="pillow", fps=4)
        print(f"✅ GIF tersimpan: {gif_path}")
    except Exception as e:
        print(f"❌ Gagal simpan GIF: {e}")
        print("   -> jalankan: pip install pillow")
        try:
            mp4_path = os.path.abspath("sequence_agent.mp4")
            anim.save(mp4_path, writer="ffmpeg", fps=4)
            print(f"✅ MP4 tersimpan: {mp4_path}")
        except Exception as e2:
            print(f"❌ ffmpeg juga gagal: {e2}")

    # --- 2. Buka otomatis di viewer default OS ---
    if os.path.exists(gif_path):
        if sys.platform.startswith("win"):
            os.startfile(gif_path)
        elif sys.platform == "darwin":
            os.system(f"open '{gif_path}'")
        else:
            os.system(f"xdg-open '{gif_path}' 2>/dev/null &")

    # --- 3. Baru show (kalau ada GUI backend) ---
    plt.show(block=True)