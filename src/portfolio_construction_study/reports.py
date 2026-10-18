"""White-background SVG and PNG charts for the portfolio study."""

from __future__ import annotations

import struct
import zlib
from html import escape
from pathlib import Path

W, H = 960, 540
BLUE, ORANGE, NAVY, GRID = "#2878b5", "#df7b36", "#18324f", "#e7edf2"
FONT = {
    "A": ("010", "101", "111", "101", "101"), "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"), "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"), "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"), "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"), "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "101", "110", "101", "101"), "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"), "N": ("101", "111", "111", "111", "101"),
    "O": ("010", "101", "101", "101", "010"), "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "111", "011"), "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"), "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"), "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"), "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"), "Z": ("111", "001", "010", "100", "111"),
    "0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"),
    "2": ("110", "001", "010", "100", "111"), "3": ("110", "001", "010", "001", "110"),
    "4": ("101", "101", "111", "001", "001"), "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "110", "101", "010"), "7": ("111", "001", "010", "010", "010"),
    "8": ("010", "101", "010", "101", "010"), "9": ("010", "101", "011", "001", "110"),
    ".": ("000", "000", "000", "000", "010"), "-": ("000", "000", "111", "000", "000"),
    "%": ("101", "001", "010", "100", "101"), " ": ("000",) * 5,
}


class Raster:
    def __init__(self) -> None:
        self.data = bytearray([255] * W * H * 3)

    def point(self, x: int, y: int, color: str) -> None:
        if 0 <= x < W and 0 <= y < H:
            pos = (y * W + x) * 3
            self.data[pos : pos + 3] = bytes(int(color[i : i + 2], 16) for i in (1, 3, 5))

    def line(self, x1: int, y1: int, x2: int, y2: int, color: str, width: int = 1) -> None:
        dx, dy = abs(x2 - x1), -abs(y2 - y1)
        sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
        error = dx + dy
        while True:
            for ox in range(-(width // 2), width // 2 + 1):
                for oy in range(-(width // 2), width // 2 + 1):
                    self.point(x1 + ox, y1 + oy, color)
            if x1 == x2 and y1 == y2:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x1 += sx
            if twice <= dx:
                error += dx
                y1 += sy

    def rect(self, x: int, y: int, width: int, height: int, color: str) -> None:
        for row in range(y, y + height):
            for col in range(x, x + width):
                self.point(col, row, color)

    def text(self, x: int, y: int, value: str, color: str = NAVY, scale: int = 2) -> None:
        cursor = x
        for character in value.upper():
            for row, pattern in enumerate(FONT.get(character, FONT[" "])):
                for column, bit in enumerate(pattern):
                    if bit == "1":
                        for dy in range(scale):
                            for dx in range(scale):
                                self.point(cursor + column * scale + dx, y + row * scale + dy, color)
            cursor += 4 * scale

    def save(self, path: Path) -> None:
        raw = b"".join(b"\0" + self.data[y * W * 3 : (y + 1) * W * 3] for y in range(H))

        def chunk(kind: bytes, payload: bytes) -> bytes:
            body = kind + payload
            return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))

        path.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">2I5B", W, H, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b"")
        )


def _chart_svg(
    title: str,
    rows: list[dict[str, float]],
    metrics: dict[str, object],
    workflow: bool = False,
) -> str:
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="48" y="54" font-family="Arial" font-size="25" font-weight="bold" fill="{NAVY}">{escape(title)}</text>',
    ]
    if workflow:
        labels = ["Synthetic returns", "Estimate risk", "Set capped weights", "Compare outcomes"]
        for index, label in enumerate(labels):
            x = 55 + index * 220
            elements.append(f'<rect x="{x}" y="100" width="175" height="65" rx="12" fill="#f4f7fa" stroke="{BLUE}" stroke-width="2"/>')
            elements.append(f'<text x="{x + 15}" y="140" font-family="Arial" font-size="15" fill="{NAVY}">{escape(label)}</text>')
            if index < len(labels) - 1:
                elements.append(f'<path d="M{x + 176} 132h35l-8-7m8 7-8 7" fill="none" stroke="{ORANGE}" stroke-width="3"/>')
        elements.append('<text x="80" y="285" font-family="Arial" font-size="17" fill="#283746">Illustrative cumulative growth (chart below)</text>')
    strategies = metrics["strategies"]
    metric_values = [
        ("EQ RETURN", strategies["equal_weight"]["total_return"]),
        ("IV RETURN", strategies["inverse_vol"]["total_return"]),
        ("IV VOL", strategies["inverse_vol"]["annualized_volatility"]),
        ("IV SHARPE", strategies["inverse_vol"]["annualized_sharpe_zero_rf"]),
        ("IV MAX DD", strategies["inverse_vol"]["maximum_drawdown"]),
    ]
    card_y = 185 if workflow else 85
    for index, (label, value) in enumerate(metric_values):
        x = 30 + index * 182
        rendered_value = f"{value:.2f}" if label == "IV SHARPE" else f"{value:.2%}"
        elements.extend(
            [
                f'<rect x="{x}" y="{card_y}" width="166" height="64" rx="8" fill="#f4f7fa" stroke="{GRID}"/>',
                f'<text x="{x + 12}" y="{card_y + 24}" font-family="Arial" font-size="13" fill="#596b7a">{label}</text>',
                f'<text x="{x + 12}" y="{card_y + 48}" font-family="Arial" font-size="19" font-weight="bold" fill="{NAVY}">{rendered_value}</text>',
            ]
        )
    curves = {}
    for key, color in (("equal_weight", BLUE), ("inverse_vol", ORANGE)):
        wealth = 1.0
        values = [wealth]
        for row in rows:
            wealth *= 1 + float(row[key])
            values.append(wealth)
        low, high = min(values), max(values)
        if high == low:
            high = low + 1
        points = [
            (90 + i * 790 / max(1, len(values) - 1), 465 - (v - low) / (high - low) * (145 if workflow else 245))
            for i, v in enumerate(values)
        ]
        curves[key] = points
        elements.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="3" points="'
            + " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
            + '"/>'
        )
    chart_top = 320 if workflow else 220
    elements.extend(
        [
            f'<line x1="90" y1="{chart_top}" x2="90" y2="468" stroke="{NAVY}"/>',
            f'<line x1="90" y1="468" x2="885" y2="468" stroke="{NAVY}"/>',
            f'<text x="100" y="505" font-family="Arial" font-size="14" fill="{BLUE}">Equal weight</text>',
            f'<text x="250" y="505" font-family="Arial" font-size="14" fill="{ORANGE}">Capped inverse volatility</text>',
            '<text x="590" y="505" font-family="Arial" font-size="13" fill="#596b7a">Synthetic sample; illustrative only</text>',
            '</svg>',
        ]
    )
    return "\n".join(elements)


def create_reports(
    directory: Path, rows: list[dict[str, float]], metrics: dict[str, object]
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, title, is_workflow in (
        ("overview", "PORTFOLIO CONSTRUCTION STUDY", False),
        ("workflow", "RESEARCH WORKFLOW AND OUTCOME CHART", True),
    ):
        svg = _chart_svg(title, rows, metrics, is_workflow)
        (directory / f"{name}.svg").write_text(svg, encoding="utf-8")
        raster = Raster()
        raster.text(55, 38, title, NAVY, 3)
        gridlines = (320, 360, 410, 460) if is_workflow else (220, 270, 320, 370, 420, 460)
        for y in gridlines:
            raster.line(80, y, 900, y, GRID)
        raster.line(80, 320 if is_workflow else 210, 80, 465, NAVY, 2)
        raster.line(80, 465, 900, 465, NAVY, 2)
        if is_workflow:
            labels = ("SYNTHETIC RETURNS", "ESTIMATE RISK", "SET WEIGHTS", "COMPARE")
            for index, x in enumerate((55, 275, 495, 715)):
                raster.rect(x, 100, 175, 65, "#eef3f7")
                raster.rect(x, 100, 175, 3, BLUE)
                raster.text(x + 8, 128, labels[index], NAVY, 2)
        strategies = metrics["strategies"]
        metric_values = [
            ("EQ RETURN", strategies["equal_weight"]["total_return"]),
            ("IV RETURN", strategies["inverse_vol"]["total_return"]),
            ("IV VOL", strategies["inverse_vol"]["annualized_volatility"]),
            ("IV SHARPE", strategies["inverse_vol"]["annualized_sharpe_zero_rf"]),
            ("IV MAX DD", strategies["inverse_vol"]["maximum_drawdown"]),
        ]
        card_y = 185 if is_workflow else 85
        for index, (label, value) in enumerate(metric_values):
            x = 30 + index * 182
            rendered_value = f"{value:.2f}" if label == "IV SHARPE" else f"{value:.2%}"
            raster.rect(x, card_y, 166, 64, "#f4f7fa")
            raster.text(x + 10, card_y + 9, label, "#596b7a", 2)
            raster.text(x + 10, card_y + 34, rendered_value, NAVY, 3)
        for key, color in (("equal_weight", BLUE), ("inverse_vol", ORANGE)):
            wealth = 1.0
            values = [wealth]
            for row in rows:
                wealth *= 1 + float(row[key])
                values.append(wealth)
            low, high = min(values), max(values)
            span = high - low or 1.0
            pts = [
                (90 + int(i * 790 / max(1, len(values) - 1)), 450 - int((v - low) / span * (135 if is_workflow else 230)))
                for i, v in enumerate(values)
            ]
            for start, end in zip(pts, pts[1:]):
                raster.line(*start, *end, color, 2)
        raster.save(directory / f"{name}.png")
