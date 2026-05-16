from pathlib import Path                                      # ファイルやフォルダの場所を扱う標準ライブラリ
from kivymd.app import MDApp as App                           # kivyアプリの土台となるクラス
from kivy.uix.widget import Widget                            # 画面に置ける「何もない箱」のようなもの
from kivy.uix.image import Image                              # 画面に画像を表示するための部品
from kivy.core.window import Window                           # ウインドウの大きさ等を扱うもの
from kivy.properties import BooleanProperty, NumericProperty  # 状態をプロパティとして持つために使います
from kivy.core.audio import SoundLoader                       # 音声ファイルを扱うためのもの
from kivy.clock import Clock
from kivy.graphics import PushMatrix, PopMatrix, Scale, Translate, Canvas, Color, Rectangle


#----------------------------------------------
# 画像ファイルが入っているフォルダへの「道」を作る
#----------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# assets/img フォルダまでのパスを組み立てる
ASSETS_DIR = BASE_DIR / 'assets'
IMG_DIR = ASSETS_DIR / 'img'
BGM_DIR = ASSETS_DIR / 'bgm'


def first_existing(*candidates: Path) -> str:
    """候補の中から、最初に見つかったファイルパスを返す"""
    for p in candidates:
        if p.is_file():
            return str(p)

    raise FileNotFoundError(
        "必要なファイルが見つかりません。assets/img と bgm を確認してください。"
    )


def find_bgm() -> str:
    """BGMファイルを探す"""
    candidates = []
    for stem in ('bgm', 'main'):
        for ext in ('ogg', 'mp3', 'wav'):
            candidates.append(BGM_DIR / f'{stem}.{ext}')
    return first_existing(*candidates)


#----------------------------------------------
# Step10 追加:
# ブロックが壊れた時に飛び散る「簡易破片」
# ここでは当たり判定を持たない、見た目専用の部品として扱います。
#----------------------------------------------
class BrickParticle(Widget):
    """
    レンガが壊れた瞬間に少しだけ飛び散る小片。

    なぜ別クラスにするのか：
    - マリオ本体やステージ本体の責務と分けるため
    - 「見た目だけの一時オブジェクト」を独立管理したいため

    入出力：
    - 入力: 初期位置(x, y), 初速(vx, vy), 生存時間(life)
    - 出力: 毎フレーム位置が変わり、寿命が尽きたら消える

    副作用：
    - ステージ上に一時的に表示される

    例外：
    - 特になし
    """

    def __init__(self, x, y, vx, vy, life=0.45, size=(10, 10), **kwargs):
        super().__init__(**kwargs)
        self.size = size
        self.pos = (x, y)
        self.vx = vx
        self.vy = vy
        self.life = life
        self.gravity = 1200.0

        # Step10 追加:
        # レンガ片っぽく見せるため、茶色系の小さな四角を描画します
        with self.canvas:
            Color(0.72, 0.42, 0.20, 1.0)  # レンガっぽい色
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_graphics, size=self._update_graphics)

    def _update_graphics(self, *args):
        """Widgetの位置や大きさが変わったら、描画も追従させる"""
        self.rect.pos = self.pos
        self.rect.size = self.size

    def step(self, dt: float) -> bool:
        """
        1フレーム分だけ破片を進める

        戻り値:
        - True  : まだ生きている
        - False : 寿命切れで消す
        """
        self.life -= dt
        if self.life <= 0:
            return False

        self.vy -= self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return True


#----------------------------------------------
# 背景画像 + 雲 + 土管 + レンガ + 主人公 を表示する
#----------------------------------------------
class StageWithBreakBlock(Widget):
    """
    Step10:
    横移動 + 横衝突 + ジャンプ / 重力 / 着地 に加えて、
    下からレンガに当たったらブロックを壊す処理を実装したステージ。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- Step09 追加 ---
        # 縦方向の速度（ジャンプ・落下に使う）
        self.vy = 0.0

        # 重力の強さ（1秒あたりどれくらい下向きに加速するか）
        self.gravity = 900.0

        # ジャンプの初速
        self.jump_power = 450.0

        # 地面やブロックの上に立っているか
        self.on_ground = False
        # -------------------

        # --- Step10 追加 ---
        # 壊れた時に飛び散る破片をまとめて管理するリスト
        self.particles = []
        # -------------------

        # 背景画像と雲画像のパスを探す
        bg_path = first_existing(IMG_DIR / 'bg.png', IMG_DIR / 'bg.jpg')
        cloud_path = first_existing(IMG_DIR / 'cloud.png')
        dokan_path = first_existing(IMG_DIR / 'dokan.png')
        brick_path = first_existing(IMG_DIR / 'brick_block.png')

        # 背景
        bg = Image(
            source=bg_path,
            allow_stretch=True,
            keep_ratio=False,
            size=Window.size,
            size_hint=(None, None),
            pos=(0, 0),
        )
        self.add_widget(bg)

        # 雲
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

        # 土管
        self.pipe = Image(
            source=dokan_path,
            size=(64, 96),
            pos=(550, 75),
            size_hint=(None, None),
        )
        self.add_widget(self.pipe)

        # レンガブロック群
        brick_y = 200
        brick_w, brick_h = 32, 32
        base_x = 300

        # --- Step09 修正 ---
        self.bricks = []
        # -------------------
        for i in range(4):
            x = base_x + i * brick_w

            brick = Image(
                source=brick_path,
                size=(brick_w, brick_h),
                pos=(x, brick_y),
                size_hint=(None, None),
            )
            self.add_widget(brick)

            # --- Step09 修正 ---
            self.bricks.append(brick)
            # -------------------

        # floor は「見えない地面」
        self.floor = Widget()
        self.floor.size = (Window.width, 80)
        self.floor.pos = (0, 0)
        self.add_widget(self.floor)

        # 主人公
        self.mario = Mario()
        self.mario.x = 120
        self.mario.y = self.floor.top
        self.add_widget(self.mario)

        # キー状態
        self.key_left = False
        self.key_right = False

        Window.bind(on_key_down=self.on_key_down, on_key_up=self.on_key_up)

        # 1/60秒ごとに更新
        Clock.schedule_interval(self.update, 1 / 60.0)

    #-----------------------------
    # Step10 追加:
    # レンガ破壊時の破片を生成する関数
    #-----------------------------
    def spawn_brick_particles(self, brick: Image):
        """
        レンガの位置をもとに、簡易破片を複数生成する

        なぜ関数に分けるのか：
        - update() を肥大化させないため
        - 「壊れた時の演出」という責務を独立させるため
        """

        # レンガを4分割したような位置から、小片を飛ばすイメージ
        particle_settings = [
            (-120, 260, brick.x + 4,  brick.y + 18),
            (-40,  330, brick.x + 18, brick.y + 20),
            (40,   300, brick.x + 6,  brick.y + 6),
            (120,  240, brick.x + 20, brick.y + 8),
        ]

        for vx, vy, px, py in particle_settings:
            particle = BrickParticle(x=px, y=py, vx=vx, vy=vy, size=(10, 10))
            self.particles.append(particle)
            self.add_widget(particle)

    #-----------------------------
    # キー入力処理
    #-----------------------------
    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        """
        キーが押された時に呼ばれる関数
        ・左矢印: 276
        ・右矢印: 275
        ・SPACE : 32
        """
        if key == 276:   # 左
            self.key_left = True

        elif key == 275: # 右
            self.key_right = True

        # --- Step09 修正 ---
        elif key == 32:  # SPACE
            # 地面・ブロック・土管など「立っている場所」ならジャンプ可能
            if self.on_ground:
                self.vy = self.jump_power
                self.on_ground = False

                # ジャンプ開始が見やすいように、少しだけ上へずらす
                self.mario.y += 4
        # -------------------

        return True

    def on_key_up(self, window, key, scancode):
        """キーが離された時に呼ばれる関数"""
        if key == 276:
            self.key_left = False
        elif key == 275:
            self.key_right = False
        return True

    #-----------------------------
    # 毎フレーム呼ばれる update
    #-----------------------------
    def update(self, dt: float):
        """
        1/60秒ごとに呼ばれる
        dt には「前回からの経過時間（秒）」が渡される
        """

        # 当たり判定を持つ壁たち
        solids = [self.pipe] + self.bricks

        vx = 0.0

        # 入力に応じて左右の速度を決める
        if self.key_left and not self.key_right:
            vx = -self.mario.speed
            self.mario.face_left()

        elif self.key_right and not self.key_left:
            vx = self.mario.speed
            self.mario.face_right()

        else:
            vx = 0.0

        #-----------------------------
        # 横移動
        #-----------------------------
        new_x = self.mario.x + vx * dt

        # 画面の左右端で止める
        new_x = max(0, min(new_x, Window.width - self.mario.width))
        self.mario.x = new_x

        #-----------------------------
        # 横方向の衝突
        # 「ブロックや土管の上空」まで当たり判定が効かないように、
        # 高さが重なっている時だけ横衝突させる
        #-----------------------------
        for solid in solids:
            vertical_overlap = (
                self.mario.top > solid.y and
                self.mario.y < solid.top
            )

            if vertical_overlap and self.mario.collide_widget(solid):
                # 右方向に動いていた場合：壁の左側で止める
                if vx > 0 and self.mario.right > solid.x:
                    self.mario.right = solid.x

                # 左方向に動いていた場合：壁の右側で止める
                elif vx < 0 and self.mario.x < solid.right:
                    self.mario.x = solid.right

        #-----------------------------
        # 重力
        #-----------------------------
        self.vy -= self.gravity * dt

        # 縦方向の移動
        self.mario.y += self.vy * dt

        #-----------------------------
        # ジャンプ中の画像切り替え
        #-----------------------------
        if self.vy > 0:
            self.mario.set_jump(True)
        else:
            self.mario.set_jump(False)

        #-----------------------------
        # 接地状態は毎フレームいったん解除してから、
        # 床やブロック上に乗っていたら True に戻す
        #-----------------------------
        self.on_ground = False

        #-----------------------------
        # 床との衝突
        #-----------------------------
        if self.mario.y <= self.floor.top:
            self.mario.y = self.floor.top
            self.vy = 0
            self.on_ground = True

        # --- Step10 追加 ---
        # 下から当たって壊す対象を一時的に集める箱
        # ループ中に self.bricks を直接削除すると不安定になるため、
        # まずは候補だけ集め、ループ後にまとめて消します
        break_targets = []
        # -------------------

        #-----------------------------
        # 縦方向の衝突
        #-----------------------------
        for solid in solids:
            if self.mario.collide_widget(solid):

                # --- Step10 追加 ---
                # 上昇中にレンガの下面へ当たったら、そのレンガを壊す
                # pipe は壊さないので、brick だけを対象にします
                if self.vy > 0 and solid in self.bricks:
                    # マリオの頭がレンガの下面に当たった位置で止める
                    self.mario.top = solid.y

                    # それ以上めり込まないよう、上向き速度を止める
                    self.vy = 0

                    # ループが終わった後に削除するため、候補へ追加
                    break_targets.append(solid)
                # -------------------

                # --- Step09 既存処理 ---
                # 落下中で、ブロックや土管の上に着地した場合
                elif self.vy < 0 and self.mario.y <= solid.y + solid.height:
                    self.mario.y = solid.y + solid.height
                    self.vy = 0
                    self.on_ground = True
                # -------------------

        # --- Step10 追加 ---
        # 実際にレンガを壊す処理
        # 見た目から消し、当たり判定対象からも外します
        for brick in break_targets:
            if brick in self.bricks:
                self.spawn_brick_particles(brick)  # 砕け散る簡易演出
                self.remove_widget(brick)
                self.bricks.remove(brick)
        # -------------------

        # --- Step10 追加 ---
        # 破片アニメーション更新
        # 寿命が切れた破片は画面から除去します
        alive_particles = []
        for particle in self.particles:
            if particle.step(dt):
                alive_particles.append(particle)
            else:
                self.remove_widget(particle)
        self.particles = alive_particles
        # -------------------


class Mario(Image):
    """
    左右に歩ける主人公クラス

    なぜこの書き方か：
    - 表示部品(Image)として扱いたい
    - 速度や向きなど、主人公だけの状態を持たせたい

    入出力：
    - 入力: キー状態、位置更新
    - 出力: 向きや画像が切り替わった主人公の見た目

    副作用：
    - キャンバス変形で左右反転する
    """

    speed = NumericProperty(220.0)
    facing_left = BooleanProperty(False)

    def __init__(self, **kwargs):
        # --- Step09 修正 ---
        # 通常時とジャンプ時の画像を分けて持つ
        self.walk_texture = first_existing(IMG_DIR / 'mario.png')
        self.jump_texture = first_existing(IMG_DIR / 'mario_jump.png')
        # -------------------

        super().__init__(
            source=self.walk_texture,
            size=(64, 64),
            size_hint=(None, None),
            **kwargs
        )

        self._flipped = False  # テクスチャ左右反転させているか

        canvas: Canvas = self.canvas
        with canvas.before:
            self._push = PushMatrix()
            self._translate = Translate(0, 0, 0)
            self._scale = Scale(1, 1, 1)
        with canvas.after:
            self._pop = PopMatrix()

    # --- Step09 追加 ---
    def set_jump(self, jumping: bool):
        """ジャンプ中かどうかで画像を切り替える"""
        if jumping:
            if self.source != self.jump_texture:
                self.source = self.jump_texture
        else:
            if self.source != self.walk_texture:
                self.source = self.walk_texture
    # -------------------

    def face_left(self):
        """キャラを左向きにする"""
        if not self._flipped:
            self._scale.x = -1
            self._translate.x = self.x + self.width
            self._flipped = True

    def face_right(self):
        """キャラを右向きにする"""
        if self._flipped:
            self._scale.x = 1
            self._translate.x = 0
            self._flipped = False

    def on_pos(self, *args):
        """
        位置が変わったときに自動で呼ばれる
        反転中は、移動に合わせて補正を再計算する
        """
        if self._flipped:
            self._translate.x = self.center_x * 2
            self._scale.x = -1
        else:
            self._translate.x = 0
            self._scale.x = 1


#----------------------------------------------
# アプリ本体
#----------------------------------------------
class Step10BreakBlockApp(App):

    def build(self):
        # ウインドウの初期サイズを決める
        Window.size = (800, 540)

        # --- Step10 修正 ---
        # 実行時に教材段階が分かるよう、タイトルも Step10 に変更
        self.title = 'Pipe & Jump - Step10 Break Block'
        # -------------------

        return StageWithBreakBlock()

    def on_start(self):
        """アプリ起動時に自動的に呼ばれます。ここでBGMを鳴らします"""
        self.bgm = None

        try:
            bgm_path = find_bgm()
        except FileNotFoundError as e:
            # BGMがなくてもゲームは動いてほしいので、表示だけして止めません
            print(e)
            return

        self.bgm = SoundLoader.load(bgm_path)
        if self.bgm:
            self.bgm.loop = True
            self.bgm.play()
        else:
            print('BGMを読み込めませんでした。ファイル形式やパスを確認してください。')

    def on_stop(self):
        """アプリ終了時に自動的に呼ばれます。ここでBGMを止めます"""
        if self.bgm:
            self.bgm.stop()


if __name__ == '__main__':
    Step10BreakBlockApp().run()