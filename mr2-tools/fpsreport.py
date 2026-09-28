import csv, sys
from statistics import median

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Games\mr2-tools\fps-menu.csv"

rows = []
with open(path, newline="") as f:
    for r in csv.DictReader(f):
        rows.append(r)

print("rows: %d" % len(rows))
if not rows:
    sys.exit("empty")


def nums(col):
    out = []
    for r in rows:
        v = r.get(col, "")
        if v and v not in ("NA", ""):
            try:
                out.append(float(v))
            except ValueError:
                pass
    return out


def fps_report(col, label):
    ms = nums(col)
    if len(ms) < 3:
        print("  %-26s (no data)" % label)
        return
    ms_sorted = sorted(ms)
    fps = [1000.0 / m for m in ms_sorted if m > 0]
    if not fps:
        print("  %-26s (all zero)" % label)
        return
    fps_sorted = sorted(fps)

    def pct(p):
        i = min(len(fps_sorted) - 1, int(round(p / 100.0 * (len(fps_sorted) - 1))))
        return fps_sorted[i]

    print("  %-26s n=%-5d  median=%7.1f  p1=%6.1f  p99=%7.1f  min=%6.1f  max=%7.1f" % (
        label, len(ms), median(ms and [1000.0 / m for m in ms_sorted if m > 0]),
        pct(1), pct(99), fps_sorted[0], fps_sorted[-1]))
    print("      median frame time = %.3f ms" % median(ms))


print("\nFrame rate:")
fps_report("MsBetweenPresents", "app present rate")
fps_report("MsBetweenDisplayChange", "displayed to screen")

print("\nLatency / work:")
for col, label in [("MsRenderPresentLatency", "render->display latency"),
                   ("MsCPUBusy", "CPU busy"),
                   ("MsGPUTime", "GPU time"),
                   ("MsGPULatency", "GPU latency")]:
    v = nums(col)
    if v:
        print("  %-26s median=%7.3f ms   p99=%7.3f ms" % (label, median(v), sorted(v)[int(.99 * (len(v) - 1))]))

print("\nPresent details (first row):")
r = rows[0]
for k in ("PresentRuntime", "PresentMode", "SyncInterval", "AllowsTearing", "Application"):
    print("  %-18s %s" % (k, r.get(k)))

si = set(r.get("SyncInterval") for r in rows)
at = set(r.get("AllowsTearing") for r in rows)
print("  distinct SyncInterval:", si)
print("  distinct AllowsTearing:", at)
