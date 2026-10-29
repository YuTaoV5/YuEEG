# Rev G 主板制造与装配

70 × 80 mm，4 层，1.6 mm，全部 305 个封装位于顶面；包含通孔件，不等于全部 SMT。主板电气铜形与 Rev F 相同。**68 处焊盘内过孔需要填孔封帽**，清单见 ../review/via_in_pad.json，不可按普通未处理过孔直接回流焊。

新屏幕通过 35 × 67 mm 两层载板叠装，四个 10 mm 绝缘 M2 支柱；不得再用旧 8 mm 安装说明。屏幕、载板、20 芯直通有键线缆、泡棉和支柱单独装配。BOM.csv 包含原理图器件；SMT 坐标 placement.csv 不包括通孔件与机械孔。采购及接线见 ../DISPLAY_INTEGRATION.md 和 ../ASSEMBLY_EXTRAS.csv。

原主板电源、隔离槽、爬电距离、极性、板厂工艺要求见 ../reference/REV_F_BASELINE_ASSEMBLY.md；其中旧显示屏/线束/支柱条款由本文和 DISPLAY_INTEGRATION.md 替代。副板沿用 Rev F；屏幕载板不能跨接 USB 隔离域。实物装配、热和噪声仍待首板验证。
