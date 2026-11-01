# SCH16T 去耦选型与验收范围

本版已将以下型号写入数字板原理图、PCB 和 BOM。不能仅按容量与封装采购替代品；SCH16T 的内部稳压节点对有效容量和 ESR 有约束。封装变大是为了减轻直流偏压损失，不代表获得了全温度、全寿命的保证。

| 位号 | 确定型号 | 用途 | 封装／本体最大高度 |
| --- | --- | --- | --- |
| C1801 | KEMET C0805X105J5RACAUTO，1µF 50V ±5% X7R | VREGD，约1.5V | 0805 Flex，1.55mm |
| C1802 | KEMET C1206C106K3RACTU，10µF 25V ±10% X7R | VREGA，约2.5V | 1206，1.80mm |
| C1803 | KEMET C0805X105J5RACAUTO，1µF 50V ±5% X7R | V3P3 近端 | 0805 Flex，1.55mm |
| C1804、C1805 | KEMET C0603C104J5RACTU，100nF 50V ±5% X7R | V3P3／VDDIO 近端 | 0603，0.95mm |
| C1806、C1807 | KEMET C0805C475K3RACTU，4.7µF 25V ±10% X7R | LDO 输入／输出 | 0805，1.45mm |

SCH16T 的 C1/C3 有效容量窗口为0.7…1.3µF，C2 为4.6…15µF，C4/C5 为70…130nF；这些电容的 ESR 要求为1MHz下小于100mΩ。VREGD、VREGA 是芯片内部节点，不能接外部负载，也不能用系统3.3V电源直接驱动。对应本板分别为 C1801、C1802。[Murata K01 资料](https://www.murata.com.cn/-/media/webrenewal/products/sensor/pdf/datasheet/datasheet-sch16t-k01-short.ashx?cvid=20251211010000000000&la=en)

已检查 KEMET 四份规格表及第2页曲线。曲线明确标为 **Simulations**，不是批次或极限保证；它们用于排除明显不适合的选型。50V额定值本身不能证明3.3V下无容量损失。[1µF Flex](https://search.kemet.com/component-documentation/download/specsheet/C0805X105J5RACAUTO)、[100nF](https://search.kemet.com/component-documentation/download/specsheet/C0603C104J5RACTU)、[10µF](https://search.kemet.com/component-documentation/download/specsheet/C1206C106K3RACTU)、[4.7µF](https://search.kemet.com/component-documentation/download/specsheet/C0805C475K3RACTU)

作为裕量估算，若1µF电容取−5%初始容差、−15%温度变化、假设−5%偏压损失，以及从48小时基准起按3%/十倍小时估算一年老化，计算值约0.715µF；100nF取假设−2%偏压损失时约73.8nF。**假设的偏压比例不是保证下界，乘积也不是厂家联合最坏值**，因此这些计算只能说明选型方向，不能替代有效容量和 ESR 验收。温度、使用年限、交流测量条件与供应批次应在样机验证计划中明确。

PCB 保留局部电容到器件节点及地平面的连接；接地走线审查是几何筛查，不是阻抗测量。C1801 到最近连接过孔的纯走线图路径约3.07mm，U1801.13约7.18mm；铺铜连接未计入该路径，仍需在样机上检查内部稳压节点稳定性、供电纹波及显示／无线活动耦合。不得把 DRC 通过解释为电源噪声已经验证。

厂家Rev6建议的器件下方铺铜避让已合入封装，接地复核因此改为寻找接触In1／In3地填铜的过孔，不能把避让区内任意穿层过孔当作地平面入口。上述路径在更新后的筛查中仍为约3.07／7.18mm；算法不证明整个平面岛的回流分布，实际节点噪声仍需测量。

采购替代时应复核实际偏压、温度和目标寿命下的有效容量窗口、1MHz ESR、最大本体尺寸及焊盘。Flex 0805 采用本项目扩展庭院，覆盖2.35×1.55mm最大本体；普通0805庭院不能直接替代。
