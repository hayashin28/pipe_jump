from pathlib import Path             # ファイルやフォルダの場所を扱う標準ライブラリ
from kivymd.app import MDApp as App  # kivyアプリの土台となるクラス
from kivy.uix.widget import Widget   # 画面に置ける「何もない箱」のようなもの
from kivy.uix.image import Image     # 画面を表示するための部品
from kivy.core.window import Window  # ウインドウの大きさ等を扱うもの


#----------------------------------------------
# 画像ファイルが入っているフォルダへの「道」を作る
#----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# assets/img フォルダまでのパスを組み立てる
ASSETS_DIR = BASE_DIR / 'assets'
IMG_DIR = ASSETS_DIR / 'img'


def first_existing(*candidates: Path) -> str:
    
    for p in candidates:
        if p.is_file(): # 実際にそのファイルが存在するか
            return str(p)
    
    # 処理がここに来ている時点でファイルが存在しなかったことになる
    raise FileNotFoundError(
        "背景画像が見つかりません。assets/img に bg.png を置いてください。"
    )
    

#----------------------------------------------
# 画面に背景を1枚だけ出すウィジェット
#----------------------------------------------
class BackgroundOnly(Widget):
    
    def __init__(self, **kwargs):
        # 親クラス（Widget）の初期化も呼び出しておく
        super().__init__(**kwargs)
        
        # bg.png か bg.jpg のどちらでも対応できるようにする
        bg_path = first_existing(IMG_DIR / 'bg.png', IMG_DIR / 'bg.jpg')
        
        # 画像を置く部品（Image）を作る
        bg = Image(
            source=bg_path,         # 探してきた画像ファイル
            allow_stretch=True,     # 画像を引き伸ばすことを許可
            keep_ratio=False,       # 縦横比（アスペクト比）は気にしない
            size=Window.size,       # ★ ウインドウと同じサイズにする
            size_hint=(None, None), # 親（画面全体）に対して「全体いっぱい」 
            pos=(0,0),              # 左下から表示
        )
        
        # このウィジェット（画面）の上に、背景画像を乗せる
        self.add_widget(bg)

#----------------------------------------------
# アプリ本体
#----------------------------------------------
class Step01BackgroundApp(App):
    
    def build(self):
        # ウインドウの初期サイズを決める
        Window.size = (800, 540)
        # ウインドウに表示するタイトル（左上にでる）
        self.title = 'Pipe & Jump - Step01 Background'
        # 先程作った画面（BackgroundOnly）を、最初の画面として返す
        return BackgroundOnly()

if __name__ == '__main__':
    Step01BackgroundApp().run()