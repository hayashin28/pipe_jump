from pathlib import Path                                      # ファイルやフォルダの場所を扱う標準ライブラリ
from kivymd.app import MDApp as App                           # kivyアプリの土台となるクラス
from kivy.uix.widget import Widget                            # 画面に置ける「何もない箱」のようなもの
from kivy.uix.image import Image                              # 画面を表示するための部品
from kivy.core.window import Window                           # ウインドウの大きさ等を扱うもの
from kivy.properties import BooleanProperty, NumericProperty  # キャラの「向き」などを状態として持つために使います
from kivy.core.audio import SoundLoader                       # 音声ファイルを扱うためのもの
from kivy.clock import Clock
from kivy.graphics import PushMatrix, PopMatrix, Scale, Translate, Canvas

#----------------------------------------------
# 画像ファイルが入っているフォルダへの「道」を作る
#----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# assets/img フォルダまでのパスを組み立てる
ASSETS_DIR = BASE_DIR / 'assets'
IMG_DIR = ASSETS_DIR / 'img'
BGM_DIR = ASSETS_DIR / 'bgm'


def first_existing(*candidates: Path) -> str:
    
    for p in candidates:
        if p.is_file(): # 実際にそのファイルが存在するか
            return str(p)
    
    # 処理がここに来ている時点でファイルが存在しなかったことになる
    raise FileNotFoundError(
        "必要なファイルが見つかりません。assets/img と bgm を確認してください。"
    )


def find_bgm() -> str:
    """BGMファイルを探す
        優先順位
        bgm.ogg / bgm.mp3 / bgm.wav
        main.ogg / main.mp3 / main.wav
        の順に「見つかったもの」を1つ選びます。
    """
    candidates = []
    for stem in ('bgm','main'):
        for ext in ('ogg','mp3','wav'):
            candidates.append(BGM_DIR / f'{stem}.{ext}')
    return first_existing(*candidates)

#----------------------------------------------
# 背景画像 + 雲 + 土管 + レンガ + 主人公 を表示する
#----------------------------------------------
class StageWithColliedX(Widget):
    """
    横方向の当たり判定付きステージ。
    - マリオが土管やレンガにぶつかったら、それ以上は進めないようにします。
    """
    
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
        
        # 土管を一つ置く（当たり判定あり）
        # ここでは「画面の左から 550px の位置」に配置しています。
        self.pipe = Image(
            source=dokan_path,
            size=(64, 96),
            pos=(550, 75),
            size_hint=(None, None),
        )
        self.add_widget(self.pipe)

        # レンガブロックを横一列に並べる（当たり判定あり）
        # 「for ループで少しずつ x 座標をずらす」
        brick_y = 200
        brick_w, brick_h = 32, 32
        base_x = 300
        for i in range(4):
            x = base_x + i * brick_w
            # ブロックの配置位置決め            
            self.brick = Image(
                source=brick_path,
                size=(brick_w, brick_h),
                pos=(x, brick_y),
                size_hint=(None, None),
            )
            self.add_widget(self.brick)

        # ① floor を先に作る（基準）
        self.floor = Widget()
        self.floor.size = (Window.width, 80)
        self.floor.pos = (0, 0)
        self.add_widget(self.floor)
        # ② その上にマリオを置く
        self.mario = Mario()
        self.mario.x = 120
        self.mario.y = self.floor.top
        self.add_widget(self.mario)

        # キーの状態（押されている間 True になる）
        self.key_left = False
        self.key_right = False

        # キー入力イベントを受け取れるように登録する
        Window.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)
        
        # 1/60秒ごとに update() を呼んで主人公を動かす
        Clock.schedule_interval(self.update, 1 / 60.0)

    #-----------------------------
    #　キー入力処理
    #-----------------------------
    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        '''
        キーが押された時に呼ばれる関数
        
        key には 「キーの番号」が入ってくる
        ここでは、矢印の番号だけを使う
        ・左矢印：276
        ・右矢印：275
        '''
        if key == 276:   # 左
            self.key_left = True
        elif key == 275: # 右
            self.key_right = True
        return True      # イベントを「ここで終了済み」と伝える
    
    def on_key_up(self, window, key, scancode):
        ''' キーが離された時に呼ばれる関数 '''
        if key == 276:
            self.key_left = False
        elif key == 275:
            self.key_right = False
        return True


    #-----------------------------
    #　毎フレーム呼ばれる update
    #-----------------------------
    def update(self, dt: float):
        '''
        1/60秒ごとに呼ばれる
        dt には「前回からの経過時間（秒）」が渡されるので、
        speed（ピクセル/秒）* dt（秒）で移動時価を計算します
        '''
        
        solids = [self.pipe] + [self.brick] # 壁として扱うオブジェクトたち
        
        vx = 0.0
        
        # 入力に応じて左右の速度を決める
        if self.key_left and not self.key_right:
            vx = -self.mario.speed
            self.mario.face_left()

        elif self.key_right and not self.key_left:
            vx = self.mario.speed
            self.mario.face_right()

        else:
            vx = 0


        # 1フレーム分の移動量を計算
        new_x = self.mario.x + vx * dt
        
        # 画面の左右端で止める（外にはみ出さないようにする）
        new_x = max(0, min(new_x, Window.width - self.mario.width))
        
        # 計算した位置を反映
        self.mario.x = new_x
        # 壁との衝突チェック
        for solid in solids:
            if self.mario.collide_widget(solid):
                # 右方向に動いていた場合：壁の左側で止める
                if vx > 0 and self.mario.right > solid.x:
                    self.mario.right = solid.x
                # 左方向に動いていた場合：壁の右側で止める
                elif vx < 0 and self.mario.x < solid.right:
                    self.mario.x = solid.right
                    
        # y はこの step では固定のままとする（重力はまだ）
                
class Mario(Image):
    """
    左右に歩ける主人公クラス
    
    - speed: 1秒あたり何ピクセル
    - facing_left: 左を向いているか
    """
    
    speed = NumericProperty(220.0)
    facing_left = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        mario_path = first_existing(IMG_DIR / 'mario.png')        
        
        super().__init__(
            source=mario_path,
            size=(64, 64),
            size_hint=(None, None),
            **kwargs
        )
        self._flipped=False # テクスチャ左右反転させているか
        
        # スケーリング用のキャンバス命令を追加
        canvas:Canvas = self.canvas
        with canvas.before:
            self._push = PushMatrix() 
            self._translate = Translate(0, 0, 0) 
            self._scale = Scale(1, 1, 1) 
        with canvas.after:
            self._pop = PopMatrix()
    
    def face_left(self):
        """キャラを左向きにする"""
        # すでに左向きなら何もしない（無駄な反転を防ぐ）
        if not self._flipped:
            # x方向を -1 にスケール → 左右反転
            self._scale.x = -1

            # 反転すると描画原点がずれるため、
            # 位置補正として「現在位置 + 幅」だけ平行移動
            self._translate.x = self.x + self.width

            self._flipped = True


    def face_right(self):
        """キャラを右向きにする"""
        # 左向きのときだけ元に戻す
        if self._flipped:
            # 通常スケール（反転解除）
            self._scale.x = 1

            # 平行移動も元に戻す
            self._translate.x = 0

            self._flipped = False


    def on_pos(self, *args):
        """
        位置が変わったときに自動で呼ばれる（Kivyのイベント）
        反転中は、移動に合わせて補正を再計算する。
        """
        if self._flipped:
            # center_x を基準に再計算しないと、
            # 移動時にズレが発生する
            self._translate.x = self.center_x * 2
            self._scale.x = -1
        else:
            self._translate.x = 0
            self._scale.x = 1


#----------------------------------------------
# アプリ本体
#----------------------------------------------
class Step08CollideXApp(App):
        
    def build(self):
        # ウインドウの初期サイズを決める
        Window.size = (800, 540)
        # ウインドウに表示するタイトル（左上にでる）
        self.title = 'Pipe & Jump - Step08 CollideX'
        # 先程作った画面（BackgroundCloudsPipeBricks）を、最初の画面として返す
        return StageWithColliedX()

    def on_start(self):
        '''アプリ起動時に自動的にこの関数が呼ばれます。ここでBGMを鳴らします'''
        try:
            bgm_path = find_bgm()
        except FileNotFoundError as e:
            # BGMがなくてもゲームは動いてほしいので、エラーを表示するだけにして止めません。
            print(e)
            return

        self.bgm = SoundLoader.load(bgm_path)
        if self.bgm:
            self.bgm.loop = True # ループ再生を有効にする
            self.bgm.play()      # BGMを再生する
        else:
            print('BGMを読み込めませんでした。ファイル形式やパスを確認してください。')
            
    def on_stop(self):
        '''アプリ終了時に自動的にこの関数が呼ばれます。ここでBGMを止めます'''
        if self.bgm:
            self.bgm.stop()


if __name__ == '__main__':
    Step08CollideXApp().run()