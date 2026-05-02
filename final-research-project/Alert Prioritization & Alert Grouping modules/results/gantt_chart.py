from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class Task:
    id: str
    name: str
    phase: str
    start: date
    end: date
    status: str = "planned"  # planned | active | done | crit


def _day_after(d: date) -> date:
    return d + timedelta(days=1)


def _weeks(n: int) -> timedelta:
    return timedelta(days=7 * n)


def build_tasks() -> list[Task]:
    # Phase 1
    p1 = Task(
        id="p1",
        name="Literature Review",
        phase="Phase 1: Research & Planning",
        start=date(2025, 5, 1),
        end=date(2025, 6, 15),
        status="done",
    )

    p2_start = _day_after(p1.end)
    p2 = Task(
        id="p2",
        name="Problem Formulation",
        phase="Phase 1: Research & Planning",
        start=p2_start,
        end=p2_start + _weeks(2) - timedelta(days=1),
        status="done",
    )

    p3_start = _day_after(p2.end)
    p3 = Task(
        id="p3",
        name="Methodology & Dataset Selection",
        phase="Phase 1: Research & Planning",
        start=p3_start,
        end=p3_start + _weeks(2) - timedelta(days=1),
        status="done",
    )

    # Phase 2
    p4 = Task(
        id="p4",
        name="Data Merging & Labeling",
        phase="Phase 2: Data Preparation",
        start=date(2025, 7, 1),
        end=date(2025, 7, 31),
        status="active",
    )

    p5_start = _day_after(p4.end)
    p5 = Task(
        id="p5",
        name="Preprocessing & Feature Eng.",
        phase="Phase 2: Data Preparation",
        start=p5_start,
        end=p5_start + _weeks(4) - timedelta(days=1),
        status="planned",
    )

    # Phase 3
    p6_start = date(2025, 9, 1)
    p6 = Task(
        id="p6",
        name="Alert Prioritization Model",
        phase="Phase 3: Model Development",
        start=p6_start,
        end=p6_start + _weeks(6) - timedelta(days=1),
        status="planned",
    )

    p7_start = _day_after(p6.end)
    p7 = Task(
        id="p7",
        name="Alert Grouping Mechanism",
        phase="Phase 3: Model Development",
        start=p7_start,
        end=p7_start + _weeks(6) - timedelta(days=1),
        status="planned",
    )

    # Phase 4
    p8_start = date(2025, 12, 1)
    p8 = Task(
        id="p8",
        name="Model Evaluation",
        phase="Phase 4: Evaluation & Demo",
        start=p8_start,
        end=p8_start + _weeks(4) - timedelta(days=1),
        status="planned",
    )

    p9_start = _day_after(p8.end)
    p9 = Task(
        id="p9",
        name="Dashboard & Demo Dev",
        phase="Phase 4: Evaluation & Demo",
        start=p9_start,
        end=p9_start + _weeks(4) - timedelta(days=1),
        status="planned",
    )

    # Phase 5
    p10_start = date(2026, 2, 1)
    p10 = Task(
        id="p10",
        name="Final Report Writing",
        phase="Phase 5: Finalization",
        start=p10_start,
        end=p10_start + _weeks(8) - timedelta(days=1),
        status="planned",
    )

    p11_start = _day_after(p10.end)
    p11 = Task(
        id="p11",
        name="Presentation Preparation",
        phase="Phase 5: Finalization",
        start=p11_start,
        end=p11_start + _weeks(2) - timedelta(days=1),
        status="planned",
    )

    p12_start = date(2026, 4, 15)
    p12 = Task(
        id="p12",
        name="Final Submission & Viva",
        phase="Phase 5: Finalization",
        start=p12_start,
        end=p12_start + _weeks(2) - timedelta(days=1),
        status="crit",
    )

    return [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12]


def render_gantt(tasks: list[Task], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Keep the y-axis in the same order as provided (top to bottom)
    tasks_plot = list(reversed(tasks))

    phase_colors = {
        "Phase 1: Research & Planning": "#cfe2ff",
        "Phase 2: Data Preparation": "#d1e7dd",
        "Phase 3: Model Development": "#fff3cd",
        "Phase 4: Evaluation & Demo": "#e2e3e5",
        "Phase 5: Finalization": "#f8d7da",
    }

    status_edge = {
        "done": "#198754",
        "active": "#0d6efd",
        "planned": "#6c757d",
        "crit": "#dc3545",
    }

    fig_h = max(6.5, 0.55 * len(tasks_plot))
    fig, ax = plt.subplots(figsize=(14, fig_h))

    for i, t in enumerate(tasks_plot):
        left = mdates.date2num(t.start)
        width = (t.end - t.start).days + 1
        face = phase_colors.get(t.phase, "#dee2e6")
        edge = status_edge.get(t.status, "#6c757d")
        lw = 2.5 if t.status in {"active", "crit"} else 1.5

        ax.barh(
            y=i,
            width=width,
            left=left,
            height=0.55,
            color=face,
            edgecolor=edge,
            linewidth=lw,
        )

        # Task label inside the bar if it fits; otherwise left-anchored
        label = t.name
        if width >= 18:
            ax.text(
                left + width / 2,
                i,
                label,
                va="center",
                ha="center",
                fontsize=9,
            )
        else:
            ax.text(
                left + width + 2,
                i,
                label,
                va="center",
                ha="left",
                fontsize=9,
            )

    ax.set_yticks(range(len(tasks_plot)))
    ax.set_yticklabels([t.id.upper() for t in tasks_plot], fontsize=9)

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))

    ax.grid(True, axis="x", which="major", linestyle="-", linewidth=0.6, alpha=0.35)
    ax.grid(True, axis="x", which="minor", linestyle=":", linewidth=0.5, alpha=0.25)

    ax.set_title("Project Timeline – 12 Months", pad=14)
    ax.set_xlabel("Month")
    ax.set_ylabel("Task ID")

    # Tighten x-range to the visible timeline (with small padding)
    min_start = min(t.start for t in tasks)
    max_end = max(t.end for t in tasks)
    ax.set_xlim(
        mdates.date2num(min_start - timedelta(days=7)),
        mdates.date2num(max_end + timedelta(days=7)),
    )

    # Legend (phase + status key)
    phase_handles = [
        plt.Line2D([0], [0], color=c, lw=8, label=ph)
        for ph, c in phase_colors.items()
    ]
    status_handles = [
        plt.Line2D([0], [0], color=c, lw=2.5, label=s)
        for s, c in status_edge.items()
    ]

    leg1 = ax.legend(
        handles=phase_handles,
        title="Phase",
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        frameon=True,
    )
    ax.add_artist(leg1)
    ax.legend(
        handles=status_handles,
        title="Status (border)",
        loc="upper left",
        bbox_to_anchor=(1.01, 0.52),
        frameon=True,
    )

    fig.tight_layout()

    png_path = out_dir / "gantt_chart.png"
    svg_path = out_dir / "gantt_chart.svg"
    fig.savefig(png_path, dpi=200, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)

    return png_path, svg_path


def main() -> None:
    tasks = build_tasks()
    out_dir = Path(__file__).resolve().parent
    png_path, svg_path = render_gantt(tasks, out_dir)
    print(f"Wrote: {png_path}")
    print(f"Wrote: {svg_path}")


if __name__ == "__main__":
    main()
