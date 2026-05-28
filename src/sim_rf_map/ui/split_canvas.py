from tkinter import Canvas
from PIL import Image, ImageTk


class SplitOverlayCanvas(Canvas):
    """Canvas that shows two overlay images side-by-side."""

    def __init__(self, parent, width=800, height=600):
        super().__init__(parent, width=width, height=height, highlightthickness=0)
        self.overlay_a = None
        self.overlay_b = None
        self.img_a = None
        self.img_b = None
        self.bind("<Configure>", lambda e: self.redraw())

    def load_pair(self, a: Image.Image, b: Image.Image) -> None:
        self.overlay_a = a
        self.overlay_b = b
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        if self.overlay_a is None or self.overlay_b is None:
            return
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 0 or h <= 0:
            return
        half = w // 2
        a_img = self.overlay_a.resize((half, h))
        b_img = self.overlay_b.resize((w - half, h))
        self.img_a = ImageTk.PhotoImage(a_img)
        self.img_b = ImageTk.PhotoImage(b_img)
        self.create_image(0, 0, anchor="nw", image=self.img_a)
        self.create_image(half, 0, anchor="nw", image=self.img_b)
