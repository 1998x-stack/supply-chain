# 工艺关系说明
material_input：上游实际投入物，可能有配比/用量/损耗；processed_into：加工转换；uses_equipment：设备服务；byproduct_of：副产；recycled_into：闭环回收；alternative_to：替代工艺。
在现有edge表不支持的类型先保存为研究候选，不要绕过枚举硬塞成commercial_supplied_to。
危险材料例如异氰酸酯、氯、溶剂只能给工业层级概述，禁止无来源给出具体危险操作配方和条件。
对环境和资源足迹，应保存“定义的系统边界/功能单位/生产工艺/国家电力因子”，否则不比较数字。
矿产产量排名与公司份额不同；矿石品位、纯元素、精炼金属之间不能互换百分比。
