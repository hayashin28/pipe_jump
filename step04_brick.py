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
        "背景画像が見つかりません。assets/img に dokan.png を置いてください。"
    )


#----------------------------------------------
# 背景画像 + 雲 + 土管 + レンガ を表示する
#----------------------------------------------
class BackgroundCloudsPipeBricks(Widget):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 背景画像と雲画像のパスを探す
        # bg.png か bg.jpg のどちらでも対応できるようにする
        bg_path = first_existing(IMG_DIR / 'bg.png', IMG_DIR / 'bg.jpg')
        cloud_path = first_existing(IMG_DIR / 'cloud.png')
        dokan_path = first_existing(IMG_DIR / 'dokan.png')
        brick_path = first_existing(IMG_DIR / 'brick_block.png')
        
        # 先ずは背景を一番下に敷きます
        bg = Image(
            source=bg_path,         # 探してきた画像ファイル
            allow_stretch=True,     # 画像を引き伸ばすことを許可
            keep_ratio=False,       # 縦横比（アスペクト比）は気にしない
            size=Window.size,       # ★ ウインドウと同じサイズにする
            size_hint=(None, None), # 親（画面全体）に対して「全体いっぱい」 
            pos=(0,0),              # 左下から表示
        )
        self.add_widget(bg)
        
        # 雲をいくつか配置する
        # size_hint を None にして、ピクセルサイズを直接指定する。
        cloud_positions = [
            (80, 360),
            (420, 420),
            (620, 360),
        ]
        for x, y in cloud_positions:
            cloud = Image(
                source=cloud_path,
                size=(250, 96),
                pos=(x, y),
                size_hint=(None, None),
            )
            self.add_widget(cloud)
        
        # 土管を一つ置く
        # ここでは「画面の左から 550px の位置」に配置しています。
        pipe = Image(
            source=dokan_path,
            size=(64, 96),
            pos=(550, 75),
            size_hint=(None, None),
        )
        self.add_widget(pipe)

        # レンガブロックを横一列に並べる
        # 「for ループで少しずつ x 座標をずらす」
        brick_y = 200
        brick_w, brick_h = 32, 32
        base_x = 300
        for i in range(4):
            x = base_x + i * brick_w
            # ブロックの配置位置決め            
            brick = Image(
                source=brick_path,
                size=(brick_w, brick_h),
                pos=(x, brick_y),
                size_hint=(None, None),
            )
            self.add_widget(brick)

#----------------------------------------------
# アプリ本体
#----------------------------------------------
class Step04BrickApp(App):
    
    def build(self):
        # ウインドウの初期サイズを決める
        Window.size = (800, 540)
        # ウインドウに表示するタイトル（左上にでる）
        self.title = 'Pipe & Jump - Step04 Brick'
        # 先程作った画面（BackgroundCloudsPipeBricks）を、最初の画面として返す
        return BackgroundCloudsPipeBricks()

if __name__ == '__main__':
    Step04BrickApp().run()