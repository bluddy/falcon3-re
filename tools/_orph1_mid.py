import io
lines = io.open('analysis/ida_falconcd/orph1_disasm.txt', encoding='utf-8', errors='replace').read().splitlines()
starts = [i for i, ln in enumerate(lines) if ln.startswith('=' * 10) and i + 1 < len(lines)]
out = io.open('analysis/ida_falconcd/orph1_mid.txt', 'w', encoding='utf-8', newline='\n')
for si in range(34, 46):
    i = starts[si]
    out.write('--- ' + lines[i + 1].strip() + ' ---\n')
    j = i + 2
    n = 0
    while j < len(lines) and not lines[j].startswith('=' * 10) and n < 18:
        if lines[j].strip() and not lines[j].strip().startswith('---'):
            out.write(lines[j] + '\n')
            n += 1
        j += 1
    out.write('\n')
out.close()
print('ok', len(starts))
