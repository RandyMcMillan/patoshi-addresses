#!/usr/bin/env python3
"""
Plot Patoshi pubkeys and their consecutive XOR differences.

Reads a file produced by extract_patoshi_addresses.py --sort --stripped --xor,
where each line is:
    <pubkey_hex>,<xor_with_previous_pubkey_hex>

Modes:
  heatmap (default)     Two-panel byte heatmap of pubkeys and XOR differences.
  curve                 Scatter plot of the (x, y) coordinates of each pubkey
                        on secp256k1.
  xor-curve             Treat each 65-byte XOR value as a pseudo-point:
                        bytes 1-32 as "x", bytes 33-64 as "y".
  curve-combined        Pubkey points and XOR pseudo-points side by side.

Usage:
    python3 plot_patoshi_xor.py [patoshi_addresses_sorted_stripped_xor.csv]
    python3 plot_patoshi_xor.py --mode curve [patoshi_addresses_sorted_stripped_xor.csv]
    python3 plot_patoshi_xor.py --mode xor-curve [patoshi_addresses_sorted_stripped_xor.csv]
"""

import argparse
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install matplotlib numpy")
    sys.exit(1)

# secp256k1 field prime.
SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F


def load_xor_csv(path: str):
    """Load pubkey and xor hex strings from the XOR output CSV."""
    pubkeys = []
    xors = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 2:
                continue
            pubkeys.append(parts[0])
            xors.append(parts[1])
    return pubkeys, xors


def hex_to_bytes(hex_str: str, length: int = 65) -> bytes:
    """Convert a hex string to bytes, left-padding with zeros if needed."""
    b = bytes.fromhex(hex_str)
    return b.rjust(length, b"\x00")


def build_matrix(rows: list[str]) -> np.ndarray:
    """Convert a list of hex strings to a 2D uint8 array."""
    return np.array([list(hex_to_bytes(row)) for row in rows], dtype=np.uint8)


def extract_ec_point(pubkey_hex: str) -> tuple[int, int]:
    """Extract (x, y) from an uncompressed 65-byte secp256k1 public key."""
    b = hex_to_bytes(pubkey_hex, length=65)
    if b[0] != 0x04:
        raise ValueError(f"Expected uncompressed pubkey starting with 04, got {b[:1].hex()}")
    x = int.from_bytes(b[1:33], "big")
    y = int.from_bytes(b[33:65], "big")
    return x, y


def extract_pseudo_point(hex_str: str) -> tuple[int, int]:
    """Extract a pseudo (x, y) from any 65-byte hex value.

    Bytes 1-32 are treated as x and bytes 33-64 as y. The leading byte is ignored.
    """
    b = hex_to_bytes(hex_str, length=65)
    x = int.from_bytes(b[1:33], "big")
    y = int.from_bytes(b[33:65], "big")
    return x, y


def collect_points(items: list[str], extractor) -> tuple[np.ndarray, np.ndarray]:
    """Apply an extractor to each item and return normalized (x, y) arrays."""
    xs = []
    ys = []
    for item in items:
        try:
            x, y = extractor(item)
            xs.append(x)
            ys.append(y)
        except ValueError as e:
            print(f"Skipping invalid item: {e}", file=sys.stderr)

    if not xs:
        return np.array([]), np.array([])

    x_norm = np.array(xs, dtype=np.float64) / SECP256K1_P
    y_norm = np.array(ys, dtype=np.float64) / SECP256K1_P
    return x_norm, y_norm


def render_point_axes(ax_scatter, ax_hexbin, x_norm: np.ndarray, y_norm: np.ndarray, title: str):
    """Render scatter and hexbin axes for a set of normalized points."""
    ax_scatter.scatter(x_norm, y_norm, s=1, alpha=0.5, c="blue")
    ax_scatter.set_title(f"{title} ({len(x_norm)} points)")
    ax_scatter.set_xlabel("x / p")
    ax_scatter.set_ylabel("y / p")
    ax_scatter.set_xlim(0, 1)
    ax_scatter.set_ylim(0, 1)
    ax_scatter.set_aspect("equal")

    hb = ax_hexbin.hexbin(x_norm, y_norm, gridsize=50, cmap="plasma", mincnt=1)
    ax_hexbin.set_title(f"Hexbin Density: {title}")
    ax_hexbin.set_xlabel("x / p")
    ax_hexbin.set_ylabel("y / p")
    ax_hexbin.set_aspect("equal")
    return hb


def plot_heatmap(pubkeys: list[str], xors: list[str], output_png: str) -> None:
    """Generate the default two-panel byte heatmap."""
    pubkey_matrix = build_matrix(pubkeys)
    xor_matrix = build_matrix(xors)

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    im0 = axes[0].imshow(pubkey_matrix, aspect="auto", cmap="viridis", vmin=0, vmax=255)
    axes[0].set_title(f"Sorted Pubkeys ({len(pubkeys)} keys × {pubkey_matrix.shape[1]} bytes)")
    axes[0].set_ylabel("Pubkey index")
    fig.colorbar(im0, ax=axes[0], label="Byte value")

    im1 = axes[1].imshow(xor_matrix, aspect="auto", cmap="plasma", vmin=0, vmax=255)
    axes[1].set_title("XOR with Previous Sorted Pubkey")
    axes[1].set_xlabel("Byte position")
    axes[1].set_ylabel("XOR index")
    fig.colorbar(im1, ax=axes[1], label="Byte value")

    plt.tight_layout()
    plt.savefig(output_png, dpi=150)
    print(f"Saved heatmap to: {output_png}")


def plot_curve(pubkeys: list[str], output_png: str) -> None:
    """Generate a scatter plot of pubkey (x, y) coordinates on secp256k1."""
    x_norm, y_norm = collect_points(pubkeys, extract_ec_point)
    if len(x_norm) == 0:
        print("No valid uncompressed pubkeys to plot.")
        sys.exit(1)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    hb = render_point_axes(axes[0], axes[1], x_norm, y_norm, "secp256k1 Pubkey Points")
    fig.colorbar(hb, ax=axes[1], label="Count")

    plt.tight_layout()
    plt.savefig(output_png, dpi=150)
    print(f"Saved curve plot to: {output_png}")


def plot_xor_curve(xors: list[str], output_png: str) -> None:
    """Generate a scatter plot of XOR pseudo (x, y) points."""
    x_norm, y_norm = collect_points(xors, extract_pseudo_point)
    if len(x_norm) == 0:
        print("No valid XOR values to plot.")
        sys.exit(1)

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    hb = render_point_axes(
        axes[0], axes[1], x_norm, y_norm,
        "XOR Pseudo-Points (bytes 1-32 vs 33-64)"
    )
    fig.colorbar(hb, ax=axes[1], label="Count")

    plt.tight_layout()
    plt.savefig(output_png, dpi=150)
    print(f"Saved XOR curve plot to: {output_png}")


def plot_curve_combined(pubkeys: list[str], xors: list[str], output_png: str) -> None:
    """Generate a combined figure with pubkey points and XOR pseudo-points."""
    pk_x, pk_y = collect_points(pubkeys, extract_ec_point)
    xor_x, xor_y = collect_points(xors, extract_pseudo_point)

    if len(pk_x) == 0 or len(xor_x) == 0:
        print("Need both valid pubkeys and XOR values for combined plot.")
        sys.exit(1)

    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    hb0 = render_point_axes(axes[0, 0], axes[0, 1], pk_x, pk_y, "secp256k1 Pubkey Points")
    hb1 = render_point_axes(
        axes[1, 0], axes[1, 1], xor_x, xor_y,
        "XOR Pseudo-Points"
    )
    fig.colorbar(hb0, ax=axes[0, 1], label="Count")
    fig.colorbar(hb1, ax=axes[1, 1], label="Count")

    plt.tight_layout()
    plt.savefig(output_png, dpi=150)
    print(f"Saved combined curve plot to: {output_png}")


def main():
    parser = argparse.ArgumentParser(description="Plot Patoshi pubkeys and XOR differences.")
    parser.add_argument("input", nargs="?", default="patoshi_addresses_sorted_stripped_xor.csv")
    parser.add_argument(
        "--mode",
        choices=["heatmap", "curve", "xor-curve", "curve-combined"],
        default="heatmap",
        help="Plot mode: heatmap (default), curve, xor-curve, or curve-combined.",
    )
    args = parser.parse_args()

    input_path = args.input
    if not Path(input_path).exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    pubkeys, xors = load_xor_csv(input_path)
    if not pubkeys:
        print("No data found in input file.")
        sys.exit(1)

    if args.mode == "curve":
        output_png = str(Path(input_path).with_suffix("")) + "_curve.png"
        plot_curve(pubkeys, output_png)
    elif args.mode == "xor-curve":
        output_png = str(Path(input_path).with_suffix("")) + "_xor_curve.png"
        plot_xor_curve(xors, output_png)
    elif args.mode == "curve-combined":
        output_png = str(Path(input_path).with_suffix("")) + "_curve_combined.png"
        plot_curve_combined(pubkeys, xors, output_png)
    else:
        output_png = str(Path(input_path).with_suffix("")) + ".png"
        plot_heatmap(pubkeys, xors, output_png)


if __name__ == "__main__":
    main()
