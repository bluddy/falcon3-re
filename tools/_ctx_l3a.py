import io, re, sys
sys.stdout.reconfigure(encoding="utf-8")
t = io.open("registry/naming.yaml", encoding="utf-8", newline="").read()
keys = ["angle_aux_near", "angle_aux_far", "vec_transform_scale",
        "angle_xy_near", "sub_176BE", "sub_25777", "sub_3ADDA",
        "sub_4B670", "event_tone_dispatch_1d418", "stream_accumulate_driver",
        "fixed_vec_normalize_7b0e", "hw_seq_step", "sub_23AA1",
        "sub_244E8", "angle_xy_far", "sub_6D5DF", "sub_143D7"]
blocks = t.split("\n  - ")
for b in blocks:
    m = re.search(r"name: (\S+)", b)
    if m and m.group(1) in keys:
        s = re.search(r'sig: "([^"]*)"', b)
        print("##", m.group(1))
        print("  ", (s.group(1)[:420] if s else "no-sig"))