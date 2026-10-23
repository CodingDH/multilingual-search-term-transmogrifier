"""Build the article figure for the language-code pipeline's history and final form."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "docs" / "papers" / "translation-to-transmogrification" / "figures" / "analysis"
OUTPUT_STEM = OUTPUT_DIR / "language_code_pipeline_history_and_final"


COLORS = {
    "iso1": "#66727D",
    "wikimedia": "#2E7D5B",
    "iso2": "#C65D2E",
    "cldr": "#2F6DA8",
    "supplement": "#76549A",
    "enrichment": "#E9EDF1",
    "enrichment_edge": "#74808A",
    "ink": "#172235",
    "muted": "#536174",
    "track": "#E7EAEE",
    "paper": "#FFFFFF",
}


def add_box(ax, x, y, width, height, title, body, *, facecolor, edgecolor, title_color=None):
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.25,
        facecolor=facecolor,
        edgecolor=edgecolor,
    )
    ax.add_patch(box)
    ax.text(
        x + 0.025, y + height - 0.038, title,
        ha="left", va="top", fontsize=11.5, fontweight="bold",
        color=title_color or COLORS["ink"],
    )
    ax.text(
        x + 0.025, y + height - 0.085, body,
        ha="left", va="top", fontsize=9.4, linespacing=1.35,
        color=COLORS["muted"],
    )


def build_figure():
    fig = plt.figure(figsize=(15, 10), facecolor=COLORS["paper"])
    gs = fig.add_gridspec(2, 1, height_ratios=[0.9, 1.25], hspace=0.24)

    # Panel A: conceptual/historical build sequence reconstructed in Notebook 01.
    ax = fig.add_subplot(gs[0])
    ax.set_xlim(0, 940)
    ax.set_ylim(-0.9, 4.25)
    ax.axis("off")
    ax.text(0, 4.05, "A  How the target list expanded", fontsize=17, fontweight="bold", color=COLORS["ink"])
    ax.text(
        0, 3.68,
        "Historical build sequence: each stage retains earlier rows and adds languages absent from prior sources.",
        fontsize=10.5, color=COLORS["muted"],
    )

    stages = [
        ("ISO 639-1 baseline", 185, 185, COLORS["iso1"], "Original list used for the early translations"),
        ("Wikimedia", 87, 272, COLORS["wikimedia"], "Active language communities beyond the initial list"),
        ("LOC ISO 639-2", 193, 465, COLORS["iso2"], "Broader bibliographic inventory"),
        ("CLDR", 416, 881, COLORS["cldr"], "393 from CLDR 48.2 + 23 retained from CLDR 45"),
    ]
    starts = [0, 185, 272, 465]
    y_positions = [2.75, 1.85, 0.95, 0.05]

    for (name, added, cumulative, color, note), start, y in zip(stages, starts, y_positions):
        ax.add_patch(Rectangle((0, y), 881, 0.48, facecolor=COLORS["track"], edgecolor="none"))
        ax.add_patch(Rectangle((start, y), added, 0.48, facecolor=color, edgecolor="none"))
        label = f"{cumulative} total" if start == 0 else f"+{added}  →  {cumulative} total"
        if cumulative == 881:
            text_x, text_align = 868, "right"
        else:
            text_x, text_align = start + added + 14, "left"
        ax.text(text_x, y + 0.24, label, va="center", ha=text_align, fontsize=10.5, fontweight="bold", color=COLORS["ink"])
        ax.text(0, y + 0.67, name, va="bottom", ha="left", fontsize=11, fontweight="bold", color=color)
        ax.text(205, y + 0.67, note, va="bottom", ha="left", fontsize=9.5, color=COLORS["muted"])

    ax.text(881, -0.63, "Cumulative language rows", ha="right", fontsize=9.5, color=COLORS["muted"])
    for tick in [0, 185, 272, 465, 881]:
        ax.plot([tick, tick], [-0.28, -0.18], color=COLORS["muted"], linewidth=0.8)
        ax.text(tick, -0.36, str(tick), ha="center", va="top", fontsize=9, color=COLORS["muted"])
    ax.plot([0, 881], [-0.18, -0.18], color=COLORS["muted"], linewidth=0.8)

    # Panel B: current production architecture, separating row selection from enrichment.
    ax2 = fig.add_subplot(gs[1])
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    ax2.text(0, 0.97, "B  What the final pipeline uses", fontsize=17, fontweight="bold", color=COLORS["ink"])
    ax2.text(
        0, 0.915,
        "Row-defining sources establish the 881-language target set; later sources add names, families, identifiers, and service metadata.",
        fontsize=10.5, color=COLORS["muted"],
    )

    ax2.text(0, 0.835, "ROW-DEFINING SOURCES", fontsize=9.5, fontweight="bold", color=COLORS["muted"])
    source_boxes = [
        (0.00, "CLDR 48.2", "Locale inventory; scripts,\ndirectionality, modern use", "#E4EFF8", COLORS["cldr"]),
        (0.245, "LOC ISO 639-2", "ISO 639-1/2 mappings and\nbibliographic authority", "#F7E9E2", COLORS["iso2"]),
        (0.49, "Wikimedia", "Active project codes and\ncommunity infrastructure", "#E4F2EC", COLORS["wikimedia"]),
        (0.735, "CLDR 45 supplement", "23 formerly attested codes\nretained as historical evidence", "#EEE8F4", COLORS["supplement"]),
    ]
    for x, title, body, face, edge in source_boxes:
        add_box(ax2, x, 0.62, 0.225, 0.18, title, body, facecolor=face, edgecolor=edge, title_color=edge)

    for x in [0.1125, 0.3575, 0.6025, 0.8475]:
        ax2.annotate("", xy=(0.5, 0.515), xytext=(x, 0.615), arrowprops=dict(arrowstyle="->", lw=1.2, color=COLORS["muted"]))

    add_box(
        ax2, 0.315, 0.405, 0.37, 0.11,
        "881 language rows",
        "language_codes_comprehensive.csv",
        facecolor="#F4F5F6", edgecolor=COLORS["ink"], title_color=COLORS["ink"],
    )

    ax2.text(0, 0.33, "METADATA ENRICHMENT — NO NEW LANGUAGE ROWS", fontsize=9.5, fontweight="bold", color=COLORS["muted"])
    enrichment_boxes = [
        (0.00, "SIL ISO 639-3", "English names for codes\nalready selected (223 fills)"),
        (0.245, "Family evidence", "ISO 639-5 / CLDR hierarchy\n+ Glottolog classification"),
        (0.49, "Reviewed decisions", "Manual label mapping and\nrow-level reconciliation"),
        (0.735, "IANA via langcodes", "BCP 47 interoperability\n(881 tags; 16 rewrites)"),
    ]
    for x, title, body in enrichment_boxes:
        add_box(
            ax2, x, 0.095, 0.225, 0.18, title, body,
            facecolor=COLORS["enrichment"], edgecolor=COLORS["enrichment_edge"],
        )
        ax2.annotate("", xy=(x + 0.1125, 0.405), xytext=(x + 0.1125, 0.278), arrowprops=dict(arrowstyle="->", lw=1.1, color=COLORS["enrichment_edge"]))

    ax2.text(
        0, 0.025,
        "Service-support flags are attached downstream for analysis; they do not determine which languages enter the target set.",
        fontsize=9.5, color=COLORS["muted"],
    )

    fig.suptitle(
        "Language-code selection: historical expansion and final pipeline",
        x=0.06, y=0.985, ha="left", fontsize=21, fontweight="bold", color=COLORS["ink"],
    )
    fig.subplots_adjust(left=0.06, right=0.97, top=0.935, bottom=0.055)
    return fig


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig = build_figure()
    fig.savefig(OUTPUT_STEM.with_suffix(".png"), dpi=220, facecolor=fig.get_facecolor())
    fig.savefig(OUTPUT_STEM.with_suffix(".pdf"), facecolor=fig.get_facecolor())
    fig.savefig(OUTPUT_STEM.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {OUTPUT_STEM}.png, .pdf, and .svg")


if __name__ == "__main__":
    main()
