import time
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.live import Live

console = Console()

SPACE_BANNER = r"""
   _____                         
  / ____|                        
 | (___  _ __   __ _  ___ ___    
  \___ \| '_ \ / _` |/ __/ _ \   
  ____) | |_) | (_| | (_|  __/   
 |_____/| .__/ \__,_|\___\___|   
        | |                      
        |_|                      
"""


def create_starfield():
    """Create a fixed arrangement of stars and planets."""
    # Hand-crafted positions for a nice aesthetic - expanded to fill edges
    stars = [
        # Top edge stars (y=0)
        {"x": 0, "y": 0, "char": "·", "color": "white", "phase": 0},
        {"x": 2, "y": 0, "char": "✨", "color": "yellow", "phase": 0},
        {"x": 5, "y": 0, "char": "*", "color": "bright_white", "phase": 1},
        {"x": 8, "y": 0, "char": "·", "color": "white", "phase": 1},
        {"x": 11, "y": 0, "char": "✦", "color": "bright_yellow", "phase": 2},
        {"x": 15, "y": 0, "char": "★", "color": "bright_yellow", "phase": 0},
        {"x": 19, "y": 0, "char": "∘", "color": "white", "phase": 1},
        {"x": 22, "y": 0, "char": "+", "color": "yellow", "phase": 2},
        {"x": 25, "y": 0, "char": "✦", "color": "white", "phase": 2},
        {"x": 29, "y": 0, "char": "·", "color": "bright_white", "phase": 0},
        {"x": 33, "y": 0, "char": "✧", "color": "white", "phase": 1},
        {"x": 35, "y": 0, "char": "*", "color": "yellow", "phase": 1},
        {"x": 38, "y": 0, "char": "✨", "color": "bright_yellow", "phase": 2},
        {"x": 42, "y": 0, "char": "·", "color": "bright_white", "phase": 0},
        {"x": 44, "y": 0, "char": "★", "color": "yellow", "phase": 1},
        # Second row (y=1)
        {"x": 1, "y": 1, "char": "+", "color": "yellow", "phase": 1},
        {"x": 5, "y": 1, "char": "∘", "color": "white", "phase": 2},
        {"x": 9, "y": 1, "char": "·", "color": "bright_white", "phase": 0},
        {"x": 12, "y": 1, "char": "⭐", "color": "bright_yellow", "phase": 0},
        {"x": 17, "y": 1, "char": "·", "color": "white", "phase": 1},
        {"x": 23, "y": 1, "char": "✦", "color": "yellow", "phase": 2},
        {"x": 27, "y": 1, "char": "*", "color": "bright_white", "phase": 0},
        {"x": 30, "y": 1, "char": "✧", "color": "white", "phase": 1},
        {"x": 36, "y": 1, "char": "∘", "color": "bright_yellow", "phase": 2},
        {"x": 40, "y": 1, "char": "*", "color": "yellow", "phase": 2},
        {"x": 43, "y": 1, "char": "·", "color": "white", "phase": 0},
        # Left edge (various y positions)
        {"x": 0, "y": 2, "char": "✦", "color": "yellow", "phase": 2},
        {"x": 0, "y": 3, "char": "✦", "color": "bright_yellow", "phase": 0},
        {"x": 0, "y": 4, "char": "*", "color": "white", "phase": 1},
        {"x": 1, "y": 5, "char": "·", "color": "white", "phase": 1},
        {"x": 0, "y": 6, "char": "∘", "color": "bright_white", "phase": 2},
        {"x": 2, "y": 7, "char": "★", "color": "yellow", "phase": 2},
        {"x": 0, "y": 8, "char": "+", "color": "bright_yellow", "phase": 0},
        {"x": 0, "y": 9, "char": "✨", "color": "bright_yellow", "phase": 0},
        {"x": 1, "y": 10, "char": "·", "color": "white", "phase": 1},
        # Right edge (various y positions)
        {"x": 44, "y": 2, "char": "·", "color": "white", "phase": 0},
        {"x": 43, "y": 3, "char": "*", "color": "white", "phase": 1},
        {"x": 44, "y": 4, "char": "✦", "color": "bright_yellow", "phase": 2},
        {"x": 44, "y": 5, "char": "✧", "color": "bright_yellow", "phase": 2},
        {"x": 43, "y": 6, "char": "∘", "color": "white", "phase": 0},
        {"x": 43, "y": 7, "char": "⭐", "color": "yellow", "phase": 0},
        {"x": 44, "y": 8, "char": "+", "color": "bright_white", "phase": 1},
        {"x": 44, "y": 9, "char": "·", "color": "white", "phase": 1},
        {"x": 43, "y": 10, "char": "★", "color": "yellow", "phase": 2},
        # Middle fill areas
        {"x": 6, "y": 4, "char": "·", "color": "white", "phase": 1},
        {"x": 10, "y": 3, "char": "∘", "color": "bright_white", "phase": 0},
        {"x": 14, "y": 5, "char": "+", "color": "yellow", "phase": 2},
        {"x": 20, "y": 4, "char": "·", "color": "white", "phase": 1},
        {"x": 26, "y": 6, "char": "*", "color": "bright_yellow", "phase": 0},
        {"x": 32, "y": 5, "char": "✦", "color": "white", "phase": 2},
        {"x": 38, "y": 4, "char": "∘", "color": "bright_white", "phase": 2},
        {"x": 8, "y": 8, "char": "·", "color": "yellow", "phase": 0},
        {"x": 15, "y": 9, "char": "+", "color": "white", "phase": 1},
        {"x": 22, "y": 8, "char": "∘", "color": "bright_white", "phase": 2},
        {"x": 28, "y": 7, "char": "·", "color": "white", "phase": 0},
        {"x": 35, "y": 9, "char": "*", "color": "yellow", "phase": 1},
        # Lower middle area
        {"x": 5, "y": 11, "char": "✧", "color": "white", "phase": 2},
        {"x": 12, "y": 10, "char": "·", "color": "bright_yellow", "phase": 0},
        {"x": 18, "y": 11, "char": "+", "color": "yellow", "phase": 0},
        {"x": 25, "y": 10, "char": "∘", "color": "white", "phase": 1},
        {"x": 28, "y": 11, "char": "·", "color": "white", "phase": 1},
        {"x": 33, "y": 10, "char": "✦", "color": "bright_yellow", "phase": 2},
        {"x": 39, "y": 11, "char": "*", "color": "yellow", "phase": 0},
        # Bottom edge stars (y=13)
        {"x": 0, "y": 13, "char": "★", "color": "bright_yellow", "phase": 1},
        {"x": 3, "y": 13, "char": "✦", "color": "yellow", "phase": 2},
        {"x": 6, "y": 13, "char": "·", "color": "white", "phase": 0},
        {"x": 10, "y": 13, "char": "*", "color": "bright_white", "phase": 0},
        {"x": 14, "y": 13, "char": "∘", "color": "yellow", "phase": 1},
        {"x": 17, "y": 13, "char": "+", "color": "bright_white", "phase": 2},
        {"x": 20, "y": 13, "char": "✨", "color": "bright_yellow", "phase": 1},
        {"x": 24, "y": 13, "char": "·", "color": "white", "phase": 0},
        {"x": 28, "y": 13, "char": "✧", "color": "bright_yellow", "phase": 1},
        {"x": 32, "y": 13, "char": "★", "color": "white", "phase": 2},
        {"x": 36, "y": 13, "char": "*", "color": "yellow", "phase": 0},
        {"x": 39, "y": 13, "char": "∘", "color": "bright_white", "phase": 1},
        {"x": 41, "y": 13, "char": "·", "color": "yellow", "phase": 0},
        {"x": 44, "y": 13, "char": "✦", "color": "bright_yellow", "phase": 2},
    ]

    # Add a few planets in strategic positions
    planets = [
        {"x": 1, "y": 2, "char": "🌍", "is_planet": True},
        {"x": 42, "y": 2, "char": "🪐", "is_planet": True},
        {"x": 38, "y": 12, "char": "☄️", "is_planet": True},
    ]

    return stars + planets


def print_banner():
    """Print the Space ASCII banner with fixed twinkling stars and planets."""
    banner_lines = SPACE_BANNER.split("\n")
    banner_height = len(banner_lines)
    banner_width = max(len(line) for line in banner_lines)

    canvas_width = banner_width + 10
    canvas_height = banner_height + 4
    celestial_objects = create_starfield()

    # Animate for a few seconds with fixed twinkling pattern
    with Live(console=console, refresh_per_second=4) as live:
        for frame in range(12):  # ~3 seconds of animation
            # Create canvas
            canvas = [[" " for _ in range(canvas_width)] for _ in range(canvas_height)]

            # Draw stars and planets
            for obj in celestial_objects:
                x, y = obj["x"], obj["y"]
                if 0 <= y < len(canvas) and 0 <= x < len(canvas[0]):
                    # Planets always visible
                    if obj.get("is_planet"):
                        canvas[y][x] = obj["char"]
                    else:
                        # Stars twinkle in a fixed pattern based on phase
                        phase = obj.get("phase", 0)
                        if (frame + phase) % 3 != 2:  # Visible 2 out of 3 frames
                            canvas[y][x] = obj["char"]

            # Overlay the Space logo in the center
            start_y = 2
            start_x = 5

            output = Text()
            colors = ["#ff00ff", "#d700ff", "#af00ff", "#8700ff", "#5f00ff", "#0000ff"]

            for y, line in enumerate(canvas):
                for x, char in enumerate(line):
                    # Check if this position is part of the banner
                    banner_y = y - start_y
                    banner_x = x - start_x

                    if 0 <= banner_y < len(banner_lines) and 0 <= banner_x < len(
                        banner_lines[banner_y]
                    ):
                        banner_char = banner_lines[banner_y][banner_x]
                        if banner_char != " ":
                            # Draw banner character with gradient (never draw stars here)
                            color = colors[banner_y % len(colors)]
                            output.append(banner_char, style=f"bold {color}")
                        else:
                            # Empty space in banner - can draw stars/planets here
                            if char in [
                                "✨",
                                "⭐",
                                "✦",
                                "✧",
                                "★",
                                "·",
                                "*",
                                "∘",
                                "+",
                                "°",
                            ]:
                                # Find color for this star
                                for obj in celestial_objects:
                                    if (
                                        obj["x"] == x
                                        and obj["y"] == y
                                        and not obj.get("is_planet")
                                    ):
                                        output.append(char, style=obj["color"])
                                        break
                                else:
                                    output.append(char, style="yellow")
                            elif char in ["🪐", "🌍", "🌎", "🌏", "☄️"]:
                                output.append(char)
                            else:
                                output.append(char)
                    else:
                        # Outside banner area - draw stars/planets
                        if char in ["✨", "⭐", "✦", "✧", "★", "·", "*", "∘", "+", "°"]:
                            # Find color for this star
                            for obj in celestial_objects:
                                if (
                                    obj["x"] == x
                                    and obj["y"] == y
                                    and not obj.get("is_planet")
                                ):
                                    output.append(char, style=obj["color"])
                                    break
                            else:
                                output.append(char, style="yellow")
                        elif char in ["🪐", "🌍", "🌎", "🌏", "☄️"]:
                            output.append(char)
                        else:
                            output.append(char)
                output.append("\n")

            panel = Panel(
                Align.center(output),
                border_style="blue",
                padding=(0, 1),
                title="[bold cyan]v1.0[/bold cyan]",
                subtitle="[dim]As good as your LLM[/dim]",
            )
            live.update(panel)
            time.sleep(0.25)


def startup_animation():
    """Run a funky startup animation sequence."""
    steps = [
        ("Initializing core systems...", "dots"),
        ("Loading neural pathways...", "dots2"),
        ("Connecting to local model...", "bouncingBar"),
        ("Calibrating creative engines...", "material"),
    ]

    console.print()
    for text, spinner_name in steps:
        with console.status(f"[bold cyan]{text}[/bold cyan]", spinner=spinner_name):
            time.sleep(0.4)

    console.print("[bold green]✓ All systems nominal.[/bold green]\n")
