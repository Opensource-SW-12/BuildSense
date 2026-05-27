from pathlib import Path

import matplotlib
import matplotlib.font_manager as fm

_FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/malgun.ttf"),
    Path("C:/Windows/Fonts/malgunbd.ttf"),
    Path("C:/Windows/Fonts/NanumGothic.ttf"),
]


def setup_korean_font() -> None:
    matplotlib.rcParams["axes.unicode_minus"] = False

    for path in _FONT_CANDIDATES:
        if path.exists():
            fm.fontManager.addfont(str(path))
            prop = fm.FontProperties(fname=str(path))
            matplotlib.rcParams["font.family"] = prop.get_name()
            return
