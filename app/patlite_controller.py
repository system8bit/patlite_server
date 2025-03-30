import hid
from enum import Enum, Flag, auto
from typing import Dict, Optional, List
import threading


class PatliteColor(Enum):
    """パトライトの色を表す列挙型"""
    OFF = 0
    RED = 1
    GREEN = 2
    BLUE = 3
    YELLOW = 4
    PURPLE = 5
    CYAN = 6
    WHITE = 7


class PatlitePattern(Enum):
    """パトライトの点灯パターンを表す列挙型"""
    OFF = 0
    ON = 1
    BLINK = 2
    FLASH = 3


class LED(Flag):
    """LEDのビットフラグ定義"""
    NONE = 0
    RED = auto()    # 赤色LED
    YELLOW = auto() # 黄色LED
    GREEN = auto()  # 緑色LED
    BLUE = auto()   # 青色LED
    WHITE = auto()  # 白色LED


class PatliteController:
    """HIDAPIを使用してパトライトを制御するクラス"""
    
    # パトライトのVendor IDとProduct ID
    VENDOR_ID = 0x191a  # ベンダーID
    PRODUCT_ID = 0x8003  # 製品ID
    
    # ブザーモード
    BUZZER_MODE_CONTINUOUS = 0x00  # 連続動作
    BUZZER_MODE_COUNT_1 = 0x01     # 1回動作
    BUZZER_MODE_COUNT_2 = 0x02     # 2回動作
    BUZZER_MODE_COUNT_3 = 0x03     # 3回動作
    BUZZER_MODE_COUNT_4 = 0x04     # 4回動作
    BUZZER_MODE_COUNT_5 = 0x05     # 5回動作
    BUZZER_MODE_COUNT_6 = 0x06     # 6回動作
    BUZZER_MODE_COUNT_7 = 0x07     # 7回動作
    BUZZER_MODE_COUNT_8 = 0x08     # 8回動作
    BUZZER_MODE_COUNT_9 = 0x09     # 9回動作
    BUZZER_MODE_COUNT_10 = 0x0A    # 10回動作
    BUZZER_MODE_COUNT_11 = 0x0B    # 11回動作
    BUZZER_MODE_COUNT_12 = 0x0C    # 12回動作
    BUZZER_MODE_COUNT_13 = 0x0D    # 13回動作
    BUZZER_MODE_COUNT_14 = 0x0E    # 14回動作
    BUZZER_MODE_COUNT_15 = 0x0F    # 15回動作

    # ブザー音階
    BUZZER_SOUND_OFF = 0x00        # OFF
    BUZZER_SOUND_A6 = 0x01         # A6
    BUZZER_SOUND_Bb6 = 0x02        # B♭6
    BUZZER_SOUND_B6 = 0x03         # B6
    BUZZER_SOUND_C7 = 0x04         # C7
    BUZZER_SOUND_Db7 = 0x05        # D♭7
    BUZZER_SOUND_D7 = 0x06         # D7
    BUZZER_SOUND_Eb7 = 0x07        # E♭7
    BUZZER_SOUND_E7 = 0x08         # E7
    BUZZER_SOUND_F7 = 0x09         # F7
    BUZZER_SOUND_Gb7 = 0x0A        # G♭7
    BUZZER_SOUND_G7 = 0x0B         # G7
    BUZZER_SOUND_Ab7 = 0x0C        # A♭7
    BUZZER_SOUND_A7 = 0x0D         # A7
    BUZZER_SOUND_DEFAULT = 0x0E    # デフォルト値（D7: 2349.3Hz）
    BUZZER_SOUND_MAINTAIN = 0x0F   # 現在の設定を維持

    # LED制御値
    _LED_RED = 0x10                # 赤　点灯
    _LED_YELLOW = 0x01             # 黄　点灯
    _LED_GREEN = 0x10              # 緑　点灯
    _LED_BLUE = 0x01               # 青　点灯
    _LED_WHITE = 0x10              # 白　点灯
    _LED_OFF = 0x00                # 　　消灯
    
    def __init__(self):
        """コントローラの初期化"""
        self.device = None
        self.connected = False
        
        # パトライト操作用のロック
        self.lock = threading.Lock()
        
        # 現在のLED状態を保持する変数
        self.current_led_r_y = 0x00
        self.current_led_g_b = 0x00
        self.current_led_white = 0x00
        
    def connect(self) -> bool:
        """パトライトデバイスに接続する"""
        with self.lock:
            try:
                self.device = hid.device()
                self.device.open(self.VENDOR_ID, self.PRODUCT_ID)
                self.connected = True
                return True
            except Exception as e:
                print(f"接続エラー: {e}")
                return False
    
    def disconnect(self) -> None:
        """パトライトデバイスから切断する"""
        with self.lock:
            if self.connected and self.device:
                self.device.close()
                self.connected = False
    
    def set_light(self, color: PatliteColor, pattern: PatlitePattern) -> bool:
        """
        特定の色と点灯パターンでライトを設定する
        
        Args:
            color: 設定する色
            pattern: 設定する点灯パターン
            
        Returns:
            操作が成功したかどうか
        """
        with self.lock:
            if not self.connected:
                print("デバイスに接続されていません")
                return False
                
            try:
                # 色に基づいてLEDの制御値を設定
                led_r_y = 0x00  # 赤・黄LEDの制御値
                led_g_b = 0x00  # 緑・青LEDの制御値
                led_white = 0x00  # 白LEDの制御値
                
                if color == PatliteColor.RED:
                    led_r_y = self._LED_RED
                elif color == PatliteColor.YELLOW:
                    led_r_y = self._LED_YELLOW
                elif color == PatliteColor.GREEN:
                    led_g_b = self._LED_GREEN
                elif color == PatliteColor.BLUE:
                    led_g_b = self._LED_BLUE
                elif color == PatliteColor.PURPLE:
                    led_r_y = self._LED_RED
                    led_g_b = self._LED_BLUE
                elif color == PatliteColor.CYAN:
                    led_g_b = self._LED_GREEN | self._LED_BLUE
                elif color == PatliteColor.WHITE:
                    led_white = self._LED_WHITE
                
                # パターン（現在は点灯のみ対応）
                # 点滅や点灯フラッシュは今後実装予定
                
                # 現在の状態を保存
                self.current_led_r_y = led_r_y
                self.current_led_g_b = led_g_b
                self.current_led_white = led_white
                
                # コマンドデータを構築
                data = [0] * 9
                data[1] = 0x00            # コマンドバージョン（固定）
                data[2] = 0x00            # コマンドID（固定）
                data[3] = 0x00            # ブザー制御（変更なし）
                data[4] = 0x00            # ブザー音階（変更なし）
                data[5] = led_r_y         # LED制御 (赤・黄)
                data[6] = led_g_b         # LED制御 (緑・青)
                data[7] = led_white       # LED C(白)
                data[8] = 0x00            # 予備（固定）
                
                self.device.write(data)
                return True
            except Exception as e:
                print(f"ライト設定エラー: {e}")
                return False
            
    def set_leds(self, leds: LED) -> bool:
        """
        複数のLEDを同時に制御する
        
        Args:
            leds: 点灯させるLEDのフラグ組み合わせ
            
        Returns:
            操作が成功したかどうか
        """
        with self.lock:
            if not self.connected:
                print("デバイスに接続されていません")
                return False
                
            try:
                led_r_y = 0x00
                led_g_b = 0x00
                led_white = 0x00
                
                if LED.RED in leds:
                    led_r_y |= self._LED_RED
                
                if LED.YELLOW in leds:
                    led_r_y |= self._LED_YELLOW
                    
                if LED.GREEN in leds:
                    led_g_b |= self._LED_GREEN
                    
                if LED.BLUE in leds:
                    led_g_b |= self._LED_BLUE
                    
                if LED.WHITE in leds:
                    led_white |= self._LED_WHITE
                    
                # 現在の状態を保存
                self.current_led_r_y = led_r_y
                self.current_led_g_b = led_g_b
                self.current_led_white = led_white
                
                # コマンドデータを構築
                data = [0] * 9
                data[1] = 0x00            # コマンドバージョン（固定）
                data[2] = 0x00            # コマンドID（固定）
                data[3] = 0x00            # ブザー制御（変更なし）
                data[4] = 0x00            # ブザー音階（変更なし）
                data[5] = led_r_y         # LED制御 (赤・黄)
                data[6] = led_g_b         # LED制御 (緑・青)
                data[7] = led_white       # LED C(白)
                data[8] = 0x00            # 予備（固定）
                
                self.device.write(data)
                return True
            except Exception as e:
                print(f"LED設定エラー: {e}")
                return False
    
    def reset(self) -> bool:
        """全てのライトをオフにする"""
        with self.lock:
            try:
                # すべてのLEDをオフにするコマンド
                data = [0] * 9
                data[1] = 0x00            # コマンドバージョン（固定）
                data[2] = 0x00            # コマンドID（固定）
                data[3] = 0x00            # ブザー制御（オフ）
                data[4] = 0x00            # ブザー音階（オフ）
                data[5] = 0x00            # LED制御 (赤・黄) オフ
                data[6] = 0x00            # LED制御 (緑・青) オフ
                data[7] = 0x00            # LED C(白) 固定
                data[8] = 0x00            # 予備（固定）
                
                # 現在の状態をクリア
                self.current_led_r_y = 0x00
                self.current_led_g_b = 0x00
                self.current_led_white = 0x00
                
                self.device.write(data)
                return True
            except Exception as e:
                print(f"リセットエラー: {e}")
                return False
            
    def set_buzzer(self, sound: int, mode: int) -> bool:
        """
        ブザーの音と動作モードを設定する
        
        Args:
            sound: ブザー音階 (BUZZER_SOUND_*)
            mode: ブザー動作モード (BUZZER_MODE_*)
            
        Returns:
            操作が成功したかどうか
        """
        with self.lock:
            if not self.connected:
                print("デバイスに接続されていません")
                return False
                
            try:
                # コマンドデータを構築
                data = [0] * 9
                data[1] = 0x00            # コマンドバージョン（固定）
                data[2] = 0x00            # コマンドID（固定）
                data[3] = mode            # ブザー制御
                data[4] = sound           # ブザー音階
                data[5] = self.current_led_r_y  # 現在のLED状態を維持
                data[6] = self.current_led_g_b  # 現在のLED状態を維持
                data[7] = self.current_led_white  # 現在のLED状態を維持
                data[8] = 0x00            # 予備（固定）
                
                self.device.write(data)
                return True
            except Exception as e:
                print(f"ブザー設定エラー: {e}")
                return False
            
    def stop_buzzer(self) -> bool:
        """
        ブザーを停止する
        
        Returns:
            操作が成功したかどうか
        """
        return self.set_buzzer(self.BUZZER_SOUND_OFF, self.BUZZER_MODE_CONTINUOUS)
    
    def set_all(self, leds: LED, buzzer_sound: int, buzzer_mode: int) -> bool:
        """
        LEDとブザーを同時に設定する
        
        Args:
            leds: 点灯させるLEDのフラグ組み合わせ
            buzzer_sound: ブザー音階
            buzzer_mode: ブザー動作モード
            
        Returns:
            操作が成功したかどうか
        """
        with self.lock:
            if not self.connected:
                print("デバイスに接続されていません")
                return False
                
            try:
                led_r_y = 0x00
                led_g_b = 0x00
                led_white = 0x00
                
                if LED.RED in leds:
                    led_r_y |= self._LED_RED
                
                if LED.YELLOW in leds:
                    led_r_y |= self._LED_YELLOW
                    
                if LED.GREEN in leds:
                    led_g_b |= self._LED_GREEN
                    
                if LED.BLUE in leds:
                    led_g_b |= self._LED_BLUE
                    
                if LED.WHITE in leds:
                    led_white |= self._LED_WHITE
                    
                # 現在の状態を保存
                self.current_led_r_y = led_r_y
                self.current_led_g_b = led_g_b
                self.current_led_white = led_white
                
                # コマンドデータを構築
                data = [0] * 9
                data[1] = 0x00            # コマンドバージョン（固定）
                data[2] = 0x00            # コマンドID（固定）
                data[3] = buzzer_mode     # ブザー制御
                data[4] = buzzer_sound    # ブザー音階
                data[5] = led_r_y         # LED制御 (赤・黄)
                data[6] = led_g_b         # LED制御 (緑・青)
                data[7] = led_white       # LED C(白)
                data[8] = 0x00            # 予備（固定）
                
                self.device.write(data)
                return True
            except Exception as e:
                print(f"設定エラー: {e}")
                return False


# シングルトンインスタンス
patlite = PatliteController() 