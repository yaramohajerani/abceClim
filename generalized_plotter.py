import os
import argparse
from typing import List, Dict, Any

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

# Optional dependency for GIF creation
try:
    import imageio.v2 as imageio  # imageio <=3
except ImportError:  # pragma: no cover
    imageio = None

# -------------------------------------------------------------
# Helpers to load data
# -------------------------------------------------------------

def _load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Expected file not found: {path}")
    return pd.read_csv(path)


def load_results(results_dir: str) -> Dict[str, Any]:
    """Load result CSVs from *results_dir* into DataFrames.

    Returns a dict with keys:
        - results_df
        - per_type_df (optional)
        - shock_rounds (list[int])
        - network_summary_df (optional)
    """
    results = {}

    # Core aggregated time-series
    results_csv = os.path.join(results_dir, "simulation_results.csv")
    results['results_df'] = _load_csv(results_csv)

    # Optional per-type time-series
    per_type_csv = os.path.join(results_dir, "per_type_timeseries.csv")
    if os.path.exists(per_type_csv):
        results['per_type_df'] = _load_csv(per_type_csv)
    else:
        results['per_type_df'] = None

    # Shock rounds
    shock_csv = os.path.join(results_dir, "shock_rounds.csv")
    if os.path.exists(shock_csv):
        shock_df = _load_csv(shock_csv)
        results['shock_rounds'] = shock_df['round'].tolist()
    else:
        results['shock_rounds'] = []

    # Network summary (optional – for structure plot)
    network_csv = os.path.join(results_dir, "network_summary.csv")
    if os.path.exists(network_csv):
        results['network_summary_df'] = _load_csv(network_csv)
    else:
        results['network_summary_df'] = None

    return results

# -------------------------------------------------------------
# Plotting functions
# -------------------------------------------------------------

def plot_time_series(results: Dict[str, Any], output_dir: str):
    """Create aggregated and per-type time-series plots."""
    results_df: pd.DataFrame = results['results_df']
    per_type_df: pd.DataFrame | None = results.get('per_type_df')
    shock_rounds: List[int] = results.get('shock_rounds', [])

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # --------------------------------------------------
    # 2×2 aggregated metrics figure
    # --------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    def _add_shock_lines(ax):
        for sr in shock_rounds:
            ax.axvline(sr, color='red', linestyle='--', alpha=0.4)

    # Wealth
    axes[0, 0].plot(results_df['round'], results_df['total_wealth'])
    _add_shock_lines(axes[0, 0])
    axes[0, 0].set_title('Total Wealth Over Time')
    axes[0, 0].set_xlabel('Round')
    axes[0, 0].set_ylabel('Total Wealth')
    axes[0, 0].grid(True)

    # Production
    axes[0, 1].plot(results_df['round'], results_df['total_production'])
    _add_shock_lines(axes[0, 1])
    axes[0, 1].set_title('Total Production Over Time')
    axes[0, 1].set_xlabel('Round')
    axes[0, 1].set_ylabel('Total Production')
    axes[0, 1].grid(True)

    # Consumption
    axes[1, 0].plot(results_df['round'], results_df['total_consumption'])
    _add_shock_lines(axes[1, 0])
    axes[1, 0].set_title('Total Consumption Over Time')
    axes[1, 0].set_xlabel('Round')
    axes[1, 0].set_ylabel('Total Consumption')
    axes[1, 0].grid(True)

    # Trades
    axes[1, 1].plot(results_df['round'], results_df['total_trades'])
    _add_shock_lines(axes[1, 1])
    axes[1, 1].set_title('Total Trades Over Time')
    axes[1, 1].set_xlabel('Round')
    axes[1, 1].set_ylabel('Total Trades')
    axes[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'simulation_results.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)

    # --------------------------------------------------
    # Per-type metrics (if available)
    # --------------------------------------------------
    if per_type_df is not None and not per_type_df.empty:
        fig2, axes2 = plt.subplots(2, 2, figsize=(12, 8))

        def _plot_metric(ax, metric_key, title, ylabel):
            for agent_type, group_df in per_type_df.groupby('agent_type'):
                ax.plot(group_df['round'], group_df[metric_key], label=agent_type)
            _add_shock_lines(ax)
            ax.set_title(title)
            ax.set_xlabel('Round')
            ax.set_ylabel(ylabel)
            ax.grid(True)

        _plot_metric(axes2[0, 0], 'production', 'Production by Type', 'Units')
        _plot_metric(axes2[0, 1], 'wealth', 'Wealth by Type', 'Wealth')
        _plot_metric(axes2[1, 0], 'consumption', 'Consumption by Type', 'Units')
        _plot_metric(axes2[1, 1], 'trades', 'Trades by Type', '# Trades')

        handles, labels = axes2[0, 0].get_legend_handles_labels()
        fig2.legend(handles, labels, loc='lower center', ncol=len(labels))
        plt.tight_layout(rect=[0, 0.05, 1, 1])
        fig2.savefig(os.path.join(output_dir, 'metrics_by_type.png'), dpi=300, bbox_inches='tight')
        plt.close(fig2)


def plot_network_structure(results: Dict[str, Any], output_dir: str):
    """Create a static plot of the agent network structure."""
    summary_df: pd.DataFrame | None = results.get('network_summary_df')
    if summary_df is None or summary_df.empty:
        print("[Plotter] No network summary found – skipping network plot.")
        return

    # Build directed graph from edge rows
    edge_rows = summary_df[summary_df['data_type'] == 'network_edge']
    if edge_rows.empty:
        print("[Plotter] network_edge rows not found – skipping network plot.")
        return
    G = nx.DiGraph()
    for _, row in edge_rows.iterrows():
        G.add_edge(row['source'], row['target'], weight=row.get('weight', 1.0))

    # Determine positions using deterministic layout
    pos = nx.spring_layout(G, seed=42, k=0.35)

    # Node colors by agent type (encoded in node label before underscore)
    type_color = {
        'producer': 'red',
        'intermediary': 'green',
        'consumer': 'blue'
    }
    node_colors = [type_color.get(n.split('_')[0], 'gray') for n in G.nodes]

    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=300, alpha=0.9, edgecolors='black', linewidths=0.5)

    # Draw edges with widths scaled by weight (similar normalization as runner)
    weights = [data.get('weight', 1.0) for _, _, data in G.edges(data=True)]
    if weights:
        w_min, w_max = min(weights), max(weights)
        edge_widths = [0.5 + 2.5 * ((w - w_min) / (w_max - w_min + 1e-9)) for w in weights]
    else:
        edge_widths = 1.0
    nx.draw_networkx_edges(G, pos, width=edge_widths, arrows=False, alpha=0.25, edge_color='gray')

    simple_labels = {n: n.split('_')[1] for n in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=simple_labels, font_size=6)

    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], marker='o', color='w', label=typ.capitalize(),
                              markerfacecolor=col, markersize=10, markeredgecolor='black')
                       for typ, col in type_color.items()]
    plt.legend(handles=legend_elements, title='Agent Type', loc='best')

    plt.title('Agent Network Structure')
    plt.axis('off')
    plt.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'network_structure.png'), dpi=300, bbox_inches='tight')
    plt.close()


# -------------------------------------------------------------
# Network GIF (optional)
# -------------------------------------------------------------

def create_network_gif(results_dir: str, duration: float = 0.7):
    """Recreate animated GIF from saved PNG frames (if available).

    Parameters
    ----------
    results_dir : str
        Directory where the simulation stored its *network_frames* subfolder.
    duration : float, optional
        Time between frames in seconds, by default 0.7.
    """
    frames_dir = os.path.join(results_dir, "network_frames")

    if not os.path.isdir(frames_dir):
        print("[Plotter] network_frames directory not found – skipping GIF creation.")
        return

    # Collect PNG frames and ensure there are enough to animate
    frame_files = sorted([f for f in os.listdir(frames_dir) if f.lower().endswith('.png')])
    if len(frame_files) < 2:
        print("[Plotter] Not enough frames to create a GIF (need >=2).")
        return

    if imageio is None:
        print("[Plotter] imageio library not installed – cannot create GIF.")
        print("           Try 'pip install imageio[ffmpeg]' and rerun.")
        return

    gif_path = os.path.join(results_dir, "network_evolution.gif")
    try:
        with imageio.get_writer(gif_path, mode="I", duration=duration) as writer:
            for fname in frame_files:
                fp = os.path.join(frames_dir, fname)
                writer.append_data(imageio.imread(fp))
        print(f"[Plotter] Network GIF saved to {gif_path}")
    except Exception as exc:
        print(f"[Plotter] Failed to create GIF: {exc}")


# -------------------------------------------------------------
# CLI
# -------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Regenerate visualizations (and GIF) for a completed generalized simulation')
    parser.add_argument('results_dir', help='Directory containing exported simulation CSV files')
    parser.add_argument('--gif', action='store_true', help='(Re)create network_evolution.gif from saved frames')
    parser.add_argument('--duration', type=float, default=0.7, help='Frame duration for GIF (seconds)')

    args = parser.parse_args()

    results = load_results(args.results_dir)

    plot_time_series(results, args.results_dir)
    plot_network_structure(results, args.results_dir)

    if args.gif:
        create_network_gif(args.results_dir, duration=args.duration)

    print(f"Plots regenerated in {args.results_dir}")


if __name__ == '__main__':
    main() 