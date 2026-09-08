# -*- coding: utf-8 -*-
path = r"D:\项目\韩博师兄项目\铁一院\论文4---基于 RISC-V 可信执行环境的深部地下 BIM 零知识协同验证机制.txt"
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if '原等价形式为' in line and '(B_i=s_i H)' in line:
        # Keep only up to and including the first ")。" (end of OR form)
        # Good part ends at "s_i H)。" (OR form)
        j = line.find('s_i H)。')
        if j != -1:
            lines[i] = line[:j+7] + '\n'  # "s_i H)。" + newline
        break
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('OK')
