<p align="left"><img alt="OSPTEK" src="../../images/logo.png" width="200" /></p>

<h1 align="center">OSPTEK 2″ AMOLED Display 460×460 (AM200Q460460LK)</h1>

<p align="center"><b>AMOLED module · QSPI · CO5300</b></p>

<p align="center"><a href="./README.md">简体中文</a> | English · <a href="../../README_EN.md">Family index</a></p>

<p align="center">
  <img alt="Interface: QSPI" src="https://img.shields.io/badge/Interface-QSPI-27AE60?style=flat-square" />
  <img alt="Driver: CO5300" src="https://img.shields.io/badge/Driver-CO5300-E7352C?style=flat-square" />
  <img alt="Touch: CST820" src="https://img.shields.io/badge/Touch-CST820-F39C12?style=flat-square" />
</p>

<p align="center"><img alt="OSPTEK 2&quot; 460×460 AMOLED module product image" src="./images/product.png" width="640" /></p>

## Contents

- [Specifications](#specifications)
- [Resources](#resources)
- [Repository layout](#repository-layout)
- [Buy](#buy)
- [Support](#support)

---

## Specifications

| Item | Spec |
| ---- | ---- |
| Size | 2 inch |
| Type | AMOLED |
| Resolution | 460×460 |
| Outline | 38.50 x 39.20 mm |
| Active area | 35.88 x 35.88 mm |
| Interface | QSPI |
| Driver IC | CO5300 |
| Touch IC | CST820 |

> Full outline, FPC definition, power, and timing follow the product datasheet / driver IC datasheet.

## Resources

| Category | File |
| ---- | ---- |
| Datasheet | [`CO_5300_Datasheet_V0_00_20230328_07edb82936.pdf`](./datasheets/CO_5300_Datasheet_V0_00_20230328_07edb82936.pdf) |
| Datasheet | [`DS_CST_820_V1_2_e0543732ca.pdf`](./datasheets/DS_CST_820_V1_2_e0543732ca.pdf) |
| Datasheet | [`AM_200_Q460460_LK_ed30462590.pdf`](./datasheets/AM_200_Q460460_LK_ed30462590.pdf) |
| CAD file | [`AM_200_Q460460.step`](./cad/AM_200_Q460460.step) |
| Adapter materials | [`2寸屏幕转接板.PcbDoc`](./adapter/2%E5%AF%B8%E5%B1%8F%E5%B9%95%E8%BD%AC%E6%8E%A5%E6%9D%BF.PcbDoc) |
| Adapter materials | [`2寸屏幕转接板.SchDoc`](./adapter/2%E5%AF%B8%E5%B1%8F%E5%B9%95%E8%BD%AC%E6%8E%A5%E6%9D%BF.SchDoc) |
| Adapter materials | [`PCB-2.0寸AMOLED屏转接板V2.0.pdf`](./adapter/PCB-2.0%E5%AF%B8AMOLED%E5%B1%8F%E8%BD%AC%E6%8E%A5%E6%9D%BFV2.0.pdf) |

## Repository layout

```text
display-amoled-2inch-460x460/ # repo root (nav: ../../README_EN.md; sample projects under root examples/)
└── versions/
    └── AM200Q460460LK/        # full materials for this part number
        ├── README.md
        ├── README_EN.md
        ├── osptek.yml
        ├── images/
        ├── datasheets/       # product datasheet + driver/touch IC datasheets
        ├── cad/              # outline/cover CAD
        └── adapter/          # adapter board materials + photos
```

## Buy

See the [repo home page](../../README_EN.md#where-to-buy).

## Support

See the [repo home page](../../README_EN.md#support).

---

<p align="center"><sub>© 2026 OSPTEK · Materials in this repository are licensed under CC BY 4.0</sub></p>
