# Gerber 分板下单

三个 ZIP 分别上传：MAIN 70×80 mm 四层；DISPLAY 35×67 mm 两层；POWER 44×48 mm 四层（原 Rev F）。各包为扁平 Gerber + PTH/NPTH 钻孔 + gbrjob，无拼板。主板 68 处、充电副板 12 处焊盘内过孔需要填孔封帽，载板无焊盘内过孔。SMT 的 BOM/坐标及装配要求在各工程 fabrication_review/ 和 BOM.csv，不能只上传 Gerber 就视为完整贴片委托。

本批仅用于样机制造评审；屏幕母座编号方向仍需首件断电导通验证。EXPORT_MANIFEST.json 绑定源 PCB 与各包文件。检查报告不等于实物验收。
