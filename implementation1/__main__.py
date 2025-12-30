# pyright: strict
import pyxel
from .model import Model, Bots
from .controller import Bomberman
from .view import View
from .settings_loader import load_settings

HEAD_X = 150
HEAD_Y = 17
BLOCK_L = 10

def main():
    pyxel.init(150, 147, title="Bomberman Clone", fps=30, quit_key = pyxel.KEY_NONE)
    pyxel.load("sprites.pyxres")
    
    settings = load_settings()
    model = Model(HEAD_Y, BLOCK_L)
    bots = Bots(model)
    view = View(HEAD_X, HEAD_Y, BLOCK_L)
    controller = Bomberman(model, bots, view, settings, fps=30)

    pyxel.run(controller.update, controller.draw)

if __name__ == "__main__":
    main()
