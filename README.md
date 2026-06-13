# T1 俄乌装备损失率“公平比较”

数理统计大作业 T1：从估计偏误到 Poisson 区间估计。

本项目基于开源装备损失记录，比较俄乌双方在统一观察窗口内的可观测装备损失强度。核心目标不是估计真实战场总损失，而是在相同数据口径下完成点估计、区间估计、假设检验、Bootstrap 稳健性分析和装备类型分层估计。

## 研究问题

1. 在相同观察期内，双方装备损失的日均强度分别是多少？
2. Poisson 模型下，损失强度的 Wald、Score、Exact 置信区间如何给出？
3. 若假设双方损失强度相等，当前差异是否可能只是随机波动？
4. 考虑时间相关性和装备类型分层后，结论是否仍然稳定？

## 数据来源

本项目使用两类数据：

- Oryx 双方装备损失汇总页面：用于双方总量比较、Poisson 估计、区间估计、条件检验和装备类型分层。
- Kaggle / WarSpotting 逐条记录：当前文件仅包含俄方逐日记录，主要用于时间序列整理和探索性 Bootstrap 补充。

Oryx 来源页面：

- Russia: https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html
- Ukraine: https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-ukrainian.html

Kaggle 数据集：

- https://www.kaggle.com/datasets/zsoltlazar/automated-warspotting-equipment-losses

## 主要结果

统一观察期为 2022-02-24 至 2026-06-10，共 1568 天。

| 阵营 | 可观测损失数 | 日均损失强度 | Exact 95% CI |
|---|---:|---:|---:|
| Russia | 23,593 | 15.05 | [14.86, 15.24] |
| Ukraine | 11,425 | 7.29 | [7.15, 7.42] |

核心结论：

- 俄方与乌方日均损失强度比约为 2.07。
- 条件二项检验结果为 `p < 1e-939`，显著拒绝双方损失强度相等的原假设。
- 参数 Bootstrap 的强度比 95% 区间约为 `[2.02, 2.11]`。
- 探索性 Block Bootstrap + BCa 的强度比 95% 区间约为 `[1.82, 2.40]`。
- 装备类型分层显示，总体差异不是由单一装备类型独自造成。

注意：本文结论限定在“开源可观测记录”层面，不能直接等同于战场真实损失总体。

## 方法链

```text
Poisson 建模
-> MLE 点估计
-> Poisson 置信区间（Wald / Score / Exact）
-> 条件二项检验
-> 装备类型分层估计
-> Bootstrap 稳健性分析
```

## 项目结构

```text
.
├── data/
│   └── processed/              # 清洗后的数据与 Oryx 解析结果
├── outputs/
│   ├── figures/                # 统计结果图表
│   └── tables/                 # 统计结果表
├── src/                        # 数据处理、统计分析和图表生成脚本
├── README.md
└── requirements.txt
```

## 运行环境

建议使用 Python 3.10 或以上版本。

安装依赖：

```powershell
pip install -r requirements.txt
```

## 复现步骤

如需从原始数据重新生成统计结果，可按以下顺序运行：

```powershell
python src/00_inspect_raw_data.py
python src/01_load_clean_data.py
python src/02_descriptive_analysis.py
python src/03_poisson_estimation.py
python src/06_parse_oryx_summaries.py
python src/07_side_comparison_from_oryx.py
python src/08_parse_oryx_item_dates.py
python src/09_block_bootstrap_bca.py
python src/10_make_result_figures.py
```

其中：

- `07_side_comparison_from_oryx.py` 生成双方 Poisson 点估计、Wald/Score/Exact 区间和条件检验结果。
- `09_block_bootstrap_bca.py` 生成探索性 Block Bootstrap + BCa 区间。
- `10_make_result_figures.py` 生成主要结果图表。

## 输出文件

主要结果表：

- `outputs/tables/oryx_side_rate_estimates.csv`
- `outputs/tables/oryx_equal_rate_test.csv`
- `outputs/tables/oryx_category_comparison.csv`
- `outputs/tables/block_bootstrap_bca.csv`

主要图表：

- `outputs/figures/data_pipeline.png`
- `outputs/figures/oryx_total_side_comparison.png`
- `outputs/figures/method_chain_flow.png`
- `outputs/figures/rate_ci_comparison.png`
- `outputs/figures/bootstrap_rate_ratio_ci.png`
- `outputs/figures/category_rate_ratio.png`

## 分工信息

请在提交前补充小组成员姓名、学号、分工与贡献比例。
