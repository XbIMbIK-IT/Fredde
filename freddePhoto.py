from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk


SPRITES = Path(__file__).parent / "sprites"


def sprite(folder, name):
    return Image.open(
        SPRITES / folder / f"{name}.png"
    ).convert("RGBA")


def generate_fredde(fred):
    # тело
    pattern = sprite("bodyPattern", fred.bodyPattern).convert("L")

    color = Image.new(
        "RGBA",
        pattern.size,
        (*fred.color, 255)
    )

    result = Image.composite(
        color,
        Image.new("RGBA", pattern.size),
        pattern
    )

    # рот
    result.alpha_composite(
        sprite("misc", "mouth")
    )

    # глаза
    result.alpha_composite(
        sprite("eye", fred.eye)
    )

    # ресницы
    if fred.eyelash:
        result.alpha_composite(
            sprite("misc", "eyelashes")
        )

    # аксессуар на голову
    if fred.hatAcs != "none":
        result.alpha_composite(
            sprite("hatAcs", fred.hatAcs)
        )

    # аксессуар на глаза
    if fred.eyeAcs != "none":
        result.alpha_composite(
            sprite("eyeAcs", fred.eyeAcs)
        )

    # аксессуар на лицо
    if fred.faceAcs != "none":
        result.alpha_composite(
            sprite("faceAcs", fred.faceAcs)
        )

    return result


def show_fredde(fred):
    root = tk.Tk()
    root.title(fred.name)

    image = generate_fredde(fred)
    photo = ImageTk.PhotoImage(image)

    tk.Label(
        root,
        image=photo
    ).pack()

    root.mainloop()


def save_fredde(fred, path):
    generate_fredde(fred).save(path)
