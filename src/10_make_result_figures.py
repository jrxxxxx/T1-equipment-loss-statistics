from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables"
FIGURE_DIR = ROOT / "outputs" / "figures"


def svg_wrap(width: int, height: int, body: list[str]) -> str:
    style = """
    <style>
      text { font-family: Arial, "Microsoft YaHei", sans-serif; fill: #111827; }
      .title { font-size: 22px; font-weight: 700; }
      .subtitle { font-size: 13px; fill: #4b5563; }
      .box { fill: #f8fafc; stroke: #334155; stroke-width: 1.4; rx: 7; }
      .accent { fill: #eff6ff; stroke: #2563eb; stroke-width: 1.5; rx: 7; }
      .warn { fill: #fff7ed; stroke: #f97316; stroke-width: 1.5; rx: 7; }
      .arrow { stroke: #475569; stroke-width: 1.7; fill: none; marker-end: url(#arrow); }
      .axis { stroke: #94a3b8; stroke-width: 1; }
      .grid { stroke: #e5e7eb; stroke-width: 1; }
      .russia { fill: #ef4444; stroke: #b91c1c; }
      .ukraine { fill: #2563eb; stroke: #1d4ed8; }
      .ci { stroke: #111827; stroke-width: 2.2; }
      .tick { stroke: #111827; stroke-width: 2; }
      .note { font-size: 12px; fill: #6b7280; }
    </style>
    """
    defs = """
    <defs>
      <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#475569" />
      </marker>
    </defs>
    """
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n{defs}\n{style}\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def write_method_chain() -> None:
    steps = [
        ("Poisson 建模", "单位时间装备损失计数"),
        ("MLE 点估计", "lambda_hat = X / T"),
        ("Poisson 区间", "Wald / Score / Exact"),
        ("条件检验", "两独立 Poisson 率比较"),
        ("分层估计", "装备类型 / 时间段"),
        ("Bootstrap", "Block + BCa 稳健性"),
    ]
    width, height = 1180, 280
    body = [
        '<text class="title" x="590" y="34" text-anchor="middle">统计方法链</text>',
        '<text class="subtitle" x="590" y="58" text-anchor="middle">围绕教材中的点估计、最大似然估计、区间估计与大样本检验展开</text>',
    ]
    x0, y0, box_w, box_h, gap = 30, 95, 165, 86, 28
    for i, (name, desc) in enumerate(steps):
        x = x0 + i * (box_w + gap)
        cls = "accent" if i in [1, 2, 3] else "box"
        if i == 5:
            cls = "warn"
        body.append(f'<rect class="{cls}" x="{x}" y="{y0}" width="{box_w}" height="{box_h}" />')
        body.append(f'<text x="{x + box_w / 2}" y="{y0 + 35}" font-size="17" font-weight="700" text-anchor="middle">{name}</text>')
        body.append(f'<text class="subtitle" x="{x + box_w / 2}" y="{y0 + 60}" text-anchor="middle">{desc}</text>')
        if i < len(steps) - 1:
            ax = x + box_w + 5
            body.append(f'<path class="arrow" d="M {ax} {y0 + box_h / 2} L {ax + gap - 10} {y0 + box_h / 2}" />')
    body.append('<text class="note" x="590" y="235" text-anchor="middle">说明：Bootstrap 使用探索性 Block Bootstrap + BCa，因乌方逐日日期来自 Oryx 文件名推断，作为稳健性补充。</text>')
    (FIGURE_DIR / "method_chain_flow.svg").write_text(svg_wrap(width, height, body), encoding="utf-8")


def write_data_pipeline() -> None:
    width, height = 980, 360
    body = [
        '<text class="title" x="490" y="35" text-anchor="middle">数据处理流程</text>',
        '<text class="subtitle" x="490" y="60" text-anchor="middle">两类数据口径分别服务于时间序列分析与双方公平比较</text>',
    ]
    boxes = [
        (70, 105, "Kaggle / WarSpotting CSV", "俄方逐条记录：日期、类型、状态"),
        (70, 225, "Oryx 双方页面", "俄乌双方汇总与装备类型分层"),
        (390, 105, "清洗与聚合", "生成每日/每周损失序列"),
        (390, 225, "HTML 解析", "总量、状态、装备类型汇总"),
        (700, 105, "时间趋势图", "俄方逐日/每周分析"),
        (700, 225, "统计推断", "MLE、区间、检验、Bootstrap"),
    ]
    for x, y, title, desc in boxes:
        body.append(f'<rect class="box" x="{x}" y="{y}" width="220" height="78" />')
        body.append(f'<text x="{x + 110}" y="{y + 31}" font-size="16" font-weight="700" text-anchor="middle">{title}</text>')
        body.append(f'<text class="subtitle" x="{x + 110}" y="{y + 55}" text-anchor="middle">{desc}</text>')
    for y in [144, 264]:
        body.append(f'<path class="arrow" d="M 290 {y} L 382 {y}" />')
        body.append(f'<path class="arrow" d="M 610 {y} L 692 {y}" />')
    body.append('<text class="note" x="490" y="328" text-anchor="middle">主比较使用 Oryx 同来源汇总；逐日 Bootstrap 使用推断日期，需在论文中说明局限。</text>')
    (FIGURE_DIR / "data_pipeline.svg").write_text(svg_wrap(width, height, body), encoding="utf-8")


def write_rate_ci() -> None:
    rates = pd.read_csv(TABLE_DIR / "oryx_side_rate_estimates.csv")
    width, height = 900, 360
    left, right, top, bottom = 115, 50, 72, 70
    max_x = float(rates["exact_high_95"].max()) * 1.12
    plot_w = width - left - right

    def sx(value: float) -> float:
        return left + plot_w * value / max_x

    body = [
        '<text class="title" x="450" y="35" text-anchor="middle">双方日均装备损失强度估计</text>',
        '<text class="subtitle" x="450" y="58" text-anchor="middle">点估计与 Wald / Score / Exact 95% 置信区间</text>',
    ]
    for tick in range(0, int(max_x) + 1, 3):
        x = sx(tick)
        body.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-bottom}" />')
        body.append(f'<text class="note" x="{x:.1f}" y="{height-bottom+24}" text-anchor="middle">{tick}</text>')
    body.append(f'<line class="axis" x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" />')
    rows = list(rates.itertuples(index=False))
    for i, row in enumerate(rows):
        y = top + 62 + i * 110
        color_cls = "russia" if row.side == "Russia" else "ukraine"
        body.append(f'<text x="{left-20}" y="{y+5}" font-size="17" font-weight="700" text-anchor="end">{row.side}</text>')
        for j, prefix in enumerate(["wald", "score", "exact"]):
            yy = y + (j - 1) * 22
            low = getattr(row, f"{prefix}_low_95")
            high = getattr(row, f"{prefix}_high_95")
            label = prefix.capitalize()
            body.append(f'<text class="note" x="{left-20}" y="{yy+4}" text-anchor="end">{label}</text>')
            body.append(f'<line class="ci" x1="{sx(low):.1f}" y1="{yy}" x2="{sx(high):.1f}" y2="{yy}" />')
            body.append(f'<line class="tick" x1="{sx(low):.1f}" y1="{yy-7}" x2="{sx(low):.1f}" y2="{yy+7}" />')
            body.append(f'<line class="tick" x1="{sx(high):.1f}" y1="{yy-7}" x2="{sx(high):.1f}" y2="{yy+7}" />')
        body.append(f'<circle class="{color_cls}" cx="{sx(row.daily_rate):.1f}" cy="{y}" r="8" />')
        body.append(f'<text x="{sx(row.daily_rate)+14:.1f}" y="{y+5}" font-size="14">{row.daily_rate:.2f}</text>')
    body.append('<text class="note" x="450" y="338" text-anchor="middle">三种区间几乎重合，原因是计数样本量较大。</text>')
    (FIGURE_DIR / "rate_ci_comparison.svg").write_text(svg_wrap(width, height, body), encoding="utf-8")


def write_bootstrap_ratio() -> None:
    param = pd.read_csv(TABLE_DIR / "bootstrap_ci.csv").set_index("statistic")
    block = pd.read_csv(TABLE_DIR / "block_bootstrap_bca.csv").iloc[0]
    width, height = 900, 310
    left, right, top = 120, 55, 80
    x_min, x_max = 1.6, 2.55
    plot_w = width - left - right

    def sx(value: float) -> float:
        return left + plot_w * (value - x_min) / (x_max - x_min)

    body = [
        '<text class="title" x="450" y="35" text-anchor="middle">损失强度比的 Bootstrap 区间</text>',
        '<text class="subtitle" x="450" y="58" text-anchor="middle">比较参数 Bootstrap 与探索性 Block Bootstrap + BCa</text>',
    ]
    for tick in [1.6, 1.8, 2.0, 2.2, 2.4]:
        x = sx(tick)
        body.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="230" />')
        body.append(f'<text class="note" x="{x:.1f}" y="255" text-anchor="middle">{tick:.1f}</text>')
    body.append(f'<line class="axis" x1="{left}" y1="230" x2="{width-right}" y2="230" />')
    body.append(f'<line stroke="#dc2626" stroke-dasharray="5 5" x1="{sx(1):.1f}" y1="{top}" x2="{sx(1):.1f}" y2="230" />')

    entries = [
        ("参数 Bootstrap", float(param.loc["rate_ratio", "estimate"]), float(param.loc["rate_ratio", "ci_low_95"]), float(param.loc["rate_ratio", "ci_high_95"]), 125),
        ("Block Bootstrap + BCa", float(block["estimate"]), float(block["bca_low_95"]), float(block["bca_high_95"]), 185),
    ]
    for label, est, low, high, y in entries:
        body.append(f'<text x="{left-18}" y="{y+5}" font-size="15" font-weight="700" text-anchor="end">{label}</text>')
        body.append(f'<line class="ci" x1="{sx(low):.1f}" y1="{y}" x2="{sx(high):.1f}" y2="{y}" />')
        body.append(f'<line class="tick" x1="{sx(low):.1f}" y1="{y-8}" x2="{sx(low):.1f}" y2="{y+8}" />')
        body.append(f'<line class="tick" x1="{sx(high):.1f}" y1="{y-8}" x2="{sx(high):.1f}" y2="{y+8}" />')
        body.append(f'<circle fill="#7c3aed" stroke="#4c1d95" cx="{sx(est):.1f}" cy="{y}" r="8" />')
        body.append(f'<text x="{sx(high)+10:.1f}" y="{y+5}" font-size="13">[{low:.2f}, {high:.2f}]</text>')
    body.append('<text class="note" x="450" y="288" text-anchor="middle">Block + BCa 区间更宽，但仍不包含 1，支持双方损失强度存在差异。</text>')
    (FIGURE_DIR / "bootstrap_rate_ratio_ci.svg").write_text(svg_wrap(width, height, body), encoding="utf-8")


def write_category_ratio() -> None:
    data = pd.read_csv(TABLE_DIR / "oryx_category_comparison.csv")
    data = data.dropna(subset=["rate_ratio_russia_vs_ukraine"]).copy()
    data = data[data["Ukraine"] > 0]
    data["distance"] = (data["rate_ratio_russia_vs_ukraine"] - 1).abs()
    data = data.sort_values("distance", ascending=False).head(10)
    data = data.sort_values("rate_ratio_russia_vs_ukraine")

    width, height = 980, 500
    left, right, top, row_h = 300, 60, 70, 36
    x_min, x_max = 0, 5
    plot_w = width - left - right

    def sx(value: float) -> float:
        value = max(x_min, min(x_max, value))
        return left + plot_w * (value - x_min) / (x_max - x_min)

    body = [
        '<text class="title" x="490" y="34" text-anchor="middle">装备类型分层：俄/乌损失比</text>',
        '<text class="subtitle" x="490" y="58" text-anchor="middle">比值大于 1 表示俄方损失更多；小于 1 表示乌方损失更多</text>',
    ]
    for tick in range(0, 6):
        x = sx(tick)
        body.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-50}" />')
        body.append(f'<text class="note" x="{x:.1f}" y="{height-25}" text-anchor="middle">{tick}</text>')
    body.append(f'<line stroke="#111827" stroke-dasharray="4 4" x1="{sx(1):.1f}" y1="{top}" x2="{sx(1):.1f}" y2="{height-50}" />')
    for i, row in enumerate(data.itertuples(index=False)):
        y = top + 18 + i * row_h
        ratio = float(row.rate_ratio_russia_vs_ukraine)
        color = "#ef4444" if ratio >= 1 else "#2563eb"
        x1, x2 = sx(1), sx(ratio)
        body.append(f'<text x="{left-14}" y="{y+5}" font-size="13" text-anchor="end">{row.category}</text>')
        body.append(f'<line stroke="{color}" stroke-width="9" x1="{x1:.1f}" y1="{y}" x2="{x2:.1f}" y2="{y}" />')
        body.append(f'<circle fill="{color}" cx="{x2:.1f}" cy="{y}" r="6" />')
        body.append(f'<text x="{x2 + (10 if ratio >= 1 else -10):.1f}" y="{y+5}" font-size="12" text-anchor="{"start" if ratio >= 1 else "end"}">{ratio:.2f}</text>')
    body.append('<text class="note" x="490" y="482" text-anchor="middle">截取偏离 1 最大的 10 个装备类别；完整表见 oryx_category_comparison.csv。</text>')
    (FIGURE_DIR / "category_rate_ratio.svg").write_text(svg_wrap(width, height, body), encoding="utf-8")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    write_method_chain()
    write_data_pipeline()
    write_rate_ci()
    write_bootstrap_ratio()
    write_category_ratio()
    print("Saved presentation figures to outputs/figures.")


if __name__ == "__main__":
    main()
