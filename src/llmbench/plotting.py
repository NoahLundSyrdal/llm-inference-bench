from __future__ import annotations

from pathlib import Path

import pandas as pd


def generate_plots(summary_df: pd.DataFrame, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if summary_df.empty:
        return []

    # Lazy import so `llmbench check` does not pay matplotlib startup cost.
    import matplotlib
    import matplotlib.pyplot as plt

    matplotlib.use("Agg")

    paths: list[Path] = []

    latency_path = output_dir / "latency_vs_concurrency.png"
    _plot_latency(summary_df, latency_path, plt)
    paths.append(latency_path)

    throughput_path = output_dir / "throughput_vs_concurrency.png"
    _plot_metric(
        summary_df,
        y_col="throughput_tokens_per_s_mean",
        y_label="Throughput (tokens/s)",
        title="Throughput vs Concurrency",
        path=throughput_path,
        plt=plt,
    )
    paths.append(throughput_path)

    ttft_path = output_dir / "ttft_vs_concurrency.png"
    _plot_metric(
        summary_df,
        y_col="ttft_ms_p50",
        y_label="TTFT p50 (ms)",
        title="TTFT vs Concurrency",
        path=ttft_path,
        plt=plt,
    )
    paths.append(ttft_path)

    error_path = output_dir / "error_rate_vs_concurrency.png"
    _plot_metric(
        summary_df,
        y_col="error_rate",
        y_label="Error rate",
        title="Error Rate vs Concurrency",
        path=error_path,
        plt=plt,
    )
    paths.append(error_path)

    return paths


def _plot_latency(summary_df: pd.DataFrame, path: Path, plt) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    grouped = summary_df.groupby(["engine", "model", "workload_label"], dropna=False)

    for (engine, model, workload), group in grouped:
        ordered = group.sort_values("concurrency")
        label_base = f"{engine}:{model} [{workload}]"

        ax.plot(
            ordered["concurrency"],
            ordered["latency_ms_p50"],
            marker="o",
            label=f"{label_base} p50",
        )
        ax.plot(
            ordered["concurrency"],
            ordered["latency_ms_p95"],
            marker="x",
            linestyle="--",
            label=f"{label_base} p95",
        )

    ax.set_title("Latency vs Concurrency")
    ax.set_xlabel("Concurrency")
    ax.set_ylabel("Latency (ms)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _plot_metric(
    summary_df: pd.DataFrame,
    y_col: str,
    y_label: str,
    title: str,
    path: Path,
    plt,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    grouped = summary_df.groupby(["engine", "model", "workload_label"], dropna=False)

    for (engine, model, workload), group in grouped:
        ordered = group.sort_values("concurrency")
        ax.plot(
            ordered["concurrency"],
            ordered[y_col],
            marker="o",
            label=f"{engine}:{model} [{workload}]",
        )

    ax.set_title(title)
    ax.set_xlabel("Concurrency")
    ax.set_ylabel(y_label)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
