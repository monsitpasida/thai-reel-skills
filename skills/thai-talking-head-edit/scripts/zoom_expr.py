import json, sys

# Emit a zoompan filter whose zoom follows motion-plan zoom_events:
# each event drifts linearly scale_from -> scale_to; an 'ease' event blends in from the previous
# event's end scale over ease_s (cubic), a 'cut' event changes scale on its first frame.
# Usage: zoom_expr.py motion-plan.json [--eval t ...] (eval prints z at the given times instead)
mp = json.load(open(sys.argv[1]))
ev = mp["zoom_events"]
ax, ay = mp["zoom_anchor"]["x"], mp["zoom_anchor"]["y"]
w, h, fps = mp["canvas"]["width"], mp["canvas"]["height"], mp["canvas"]["fps"]
ss = mp.get("supersample", 1)

def line(e, t):
    return f"({e['scale_from']}+({e['scale_to']}-{e['scale_from']})*({t}-{e['start_s']})/{e['end_s'] - e['start_s']})"

def ease(curve, p):
    if curve == "out":
        return f"(1-pow(1-{p},3))"
    return f"if(lt({p},0.5),4*pow({p},3),1-pow(-2*{p}+2,3)/2)"

def event_expr(i, t):
    e = ev[i]
    target = line(e, t)
    if e["transition"] != "ease":
        return target
    prev = e.get("enter_from", ev[i - 1]["scale_to"] if i else e["scale_from"])
    p = f"clip(({t}-{e['start_s']})/{e['ease_s']},0,1)"
    return f"({prev}+({target}-{prev})*{ease(e.get('ease_curve', 'in_out'), p)})"

def z_expr(t="it"):
    z = event_expr(len(ev) - 1, t)
    for i in reversed(range(len(ev) - 1)):
        z = f"if(lt({t},{ev[i]['end_s']}),{event_expr(i, t)},{z})"
    return z

if "--eval" in sys.argv:
    # same formula evaluated in Python, for checking continuity and range
    import math
    def f(t):
        expr = z_expr(str(t)).replace("^", "**")
        env = {"if": lambda c, a, b: a if c else b, "lt": lambda a, b: a < b, "pow": math.pow,
               "clip": lambda x, lo, hi: min(max(x, lo), hi)}
        expr = expr.replace("if(", "if_(")
        env["if_"] = env.pop("if")
        return eval(expr, env)
    for t in sys.argv[sys.argv.index("--eval") + 1:]:
        print(f"{float(t):7.3f} {f(float(t)):.5f}")
    sys.exit()

x = f"max(0,min(iw-iw/zoom,{ax}*iw-iw/zoom/2))"
y = f"max(0,min(ih-ih/zoom,{ay}*ih-ih/zoom/2))"
pre = f"scale={w * ss}:{h * ss}:flags=lanczos," if ss > 1 else ""
print(f"{pre}zoompan=z='{z_expr()}':x='{x}':y='{y}':d=1:s={w}x{h}:fps={fps}")
