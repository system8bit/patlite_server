import hid
from enum import Enum, Flag, auto
from typing import Dict, Optional, List, Set
import threading
import functools


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


def require_connection(func):
    """
    デバイス接続状態を確認するデコレータ
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.connected:
            print("デバイスに接続されていません")
            return False
        return func(self, *args, **kwargs)
    return wrapper


class PatliteController:
    """HIDAPIを使用してパトライトを制御するクラス"""
    
    # パトライトのVendor IDとProduct ID
    VENDOR_ID = 0x191a  # ベンダーID
    PRODUCT_ID = 0x8003  # 製品ID
    
    # コマンド構造定数
    CMD_VERSION = 0x00  # コマンドバージョン
    CMD_ID = 0x00       # コマンドID
    RESERVED = 0x00     # 予約済み
    
    # ブザーモード
    class BuzzerMode:
        CONTINUOUS = 0x00  # 連続動作
        COUNT_1 = 0x01     # 1回動作
        COUNT_2 = 0x02     # 2回動作
        COUNT_3 = 0x03     # 3回動作
        COUNT_4 = 0x04     # 4回動作
        COUNT_5 = 0x05     # 5回動作
        COUNT_6 = 0x06     # 6回動作
        COUNT_7 = 0x07     # 7回動作
        COUNT_8 = 0x08     # 8回動作
        COUNT_9 = 0x09     # 9回動作
        COUNT_10 = 0x0A    # 10回動作
        COUNT_11 = 0x0B    # 11回動作
        COUNT_12 = 0x0C    # 12回動作
        COUNT_13 = 0x0D    # 13回動作
        COUNT_14 = 0x0E    # 14回動作
        COUNT_15 = 0x0F    # 15回動作

    # ブザー音階
    class BuzzerSound:
        OFF = 0x00        # OFF
        A6 = 0x01         # A6
        Bb6 = 0x02        # B♭6
        B6 = 0x03         # B6
        C7 = 0x04         # C7
        Db7 = 0x05        # D♭7
        D7 = 0x06         # D7
        Eb7 = 0x07        # E♭7
        E7 = 0x08         # E7
        F7 = 0x09         # F7
        Gb7 = 0x0A        # G♭7
        G7 = 0x0B         # G7
        Ab7 = 0x0C        # A♭7
        A7 = 0x0D         # A7
        DEFAULT = 0x0E    # デフォルト値（D7: 2349.3Hz）
        MAINTAIN = 0x0F   # 現在の設定を維持

    # LED制御値
    class LEDValue:
        RED = 0x10        # 赤　点灯
        YELLOW = 0x01     # 黄　点灯
        GREEN = 0x10      # 緑　点灯
        BLUE = 0x01       # 青　点灯
        WHITE = 0x10      # 白　点灯
        OFF = 0x00        # 　　消灯
    
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
        
    def _calculate_led_bits(self, leds: LED) -> tuple:
        """
        LEDフラグから各ビット値を計算する
        
        Args:
            leds: 点灯させるLEDのフラグ組み合わせ
            
        Returns:
            (led_r_y, led_g_b, led_white)のタプル
        """
        led_r_y = 0x00
        led_g_b = 0x00
        led_white = 0x00
        
        if LED.RED in leds:
            led_r_y |= self.LEDValue.RED
        
        if LED.YELLOW in leds:
            led_r_y |= self.LEDValue.YELLOW
            
        if LED.GREEN in leds:
            led_g_b |= self.LEDValue.GREEN
            
        if LED.BLUE in leds:
            led_g_b |= self.LEDValue.BLUE
            
        if LED.WHITE in leds:
            led_white |= self.LEDValue.WHITE
            
        return led_r_y, led_g_b, led_white
        
    def _write_command(self, buzzer_mode: int = 0x00, buzzer_sound: int = 0x00, 
                      led_r_y: int = None, led_g_b: int = None, led_white: int = None) -> bool:
        """
        パトライトに制御コマンドを送信する共通メソッド
        
        Args:
            buzzer_mode: ブザー制御値
            buzzer_sound: ブザー音階値
            led_r_y: 赤・黄LED制御値（Noneの場合は現在の状態を維持）
            led_g_b: 緑・青LED制御値（Noneの場合は現在の状態を維持）
            led_white: 白LED制御値（Noneの場合は現在の状態を維持）
            
        Returns:
            操作が成功したかどうか
        """
        if not self.connected:
            print("デバイスに接続されていません")
            return False
            
        try:
            # パラメータがNoneの場合は現在の状態を維持
            if led_r_y is not None:
                self.current_led_r_y = led_r_y
            if led_g_b is not None:
                self.current_led_g_b = led_g_b
            if led_white is not None:
                self.current_led_white = led_white
            
            # コマンドデータを構築
            data = [0] * 9
            data[1] = self.CMD_VERSION        # コマンドバージョン（固定）
            data[2] = self.CMD_ID             # コマンドID（固定）
            data[3] = buzzer_mode             # ブザー制御
            data[4] = buzzer_sound            # ブザー音階
            data[5] = self.current_led_r_y    # LED制御 (赤・黄)
            data[6] = self.current_led_g_b    # LED制御 (緑・青)
            data[7] = self.current_led_white  # LED C(白)
            data[8] = self.RESERVED           # 予備（固定）
            
            self.device.write(data)
            return True
        except Exception as e:
            print(f"コマンド送信エラー: {e}")
            return False
        
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
    
    @require_connection
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
            try:
                # 色に基づいてLEDの制御値を設定
                led_r_y = 0x00  # 赤・黄LEDの制御値
                led_g_b = 0x00  # 緑・青LEDの制御値
                led_white = 0x00  # 白LEDの制御値
                
                if color == PatliteColor.RED:
                    led_r_y = self.LEDValue.RED
                elif color == PatliteColor.YELLOW:
                    led_r_y = self.LEDValue.YELLOW
                elif color == PatliteColor.GREEN:
                    led_g_b = self.LEDValue.GREEN
                elif color == PatliteColor.BLUE:
                    led_g_b = self.LEDValue.BLUE
                elif color == PatliteColor.PURPLE:
                    led_r_y = self.LEDValue.RED
                    led_g_b = self.LEDValue.BLUE
                elif color == PatliteColor.CYAN:
                    led_g_b = self.LEDValue.GREEN | self.LEDValue.BLUE
                elif color == PatliteColor.WHITE:
                    led_white = self.LEDValue.WHITE
                
                # パターン（現在は点灯のみ対応）
                # 点滅や点灯フラッシュは今後実装予定
                
                # 共通のwrite処理を呼び出し
                return self._write_command(led_r_y=led_r_y, led_g_b=led_g_b, led_white=led_white)
            except Exception as e:
                print(f"ライト設定エラー: {e}")
                return False
            
    @require_connection
    def set_leds(self, leds: LED) -> bool:
        """
        複数のLEDを同時に制御する
        
        Args:
            leds: 点灯させるLEDのフラグ組み合わせ
            
        Returns:
            操作が成功したかどうか
        """
        with self.lock:
            try:
                # LEDビットを計算
                led_r_y, led_g_b, led_white = self._calculate_led_bits(leds)
                
                # 共通のwrite処理を呼び出し
                return self._write_command(led_r_y=led_r_y, led_g_b=led_g_b, led_white=led_white)
            except Exception as e:
                print(f"LED設定エラー: {e}")
                return False
    
    @require_connection
    def reset(self) -> bool:
        """全てのライトをオフにする"""
        with self.lock:
            try:
                # すべてのLEDとブザーをオフにする
                return self._write_command(0x00, 0x00, 0x00, 0x00, 0x00)
            except Exception as e:
                print(f"リセットエラー: {e}")
                return False
            
    @require_connection
    def set_buzzer(self, sound: int, mode: int) -> bool:
        """
        ブザーの音と動作モードを設定する
        
        Args:
            sound: ブザー音階 (BuzzerSound.*)
            mode: ブザー動作モード (BuzzerMode.*)
            
        Returns:
            操作が成功したかどうか
        """
        with self.lock:
            try:
                # 共通のwrite処理を呼び出し（LEDの状態は維持）
                return self._write_command(buzzer_mode=mode, buzzer_sound=sound)
            except Exception as e:
                print(f"ブザー設定エラー: {e}")
                return False
            
    def stop_buzzer(self) -> bool:
        """
        ブザーを停止する
        
        Returns:
            操作が成功したかどうか
        """
        return self.set_buzzer(self.BuzzerSound.OFF, self.BuzzerMode.CONTINUOUS)
    
    @require_connection
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
            try:
                # LEDビットを計算
                led_r_y, led_g_b, led_white = self._calculate_led_bits(leds)
                
                # 共通のwrite処理を呼び出し
                return self._write_command(
                    buzzer_mode=buzzer_mode, 
                    buzzer_sound=buzzer_sound, 
                    led_r_y=led_r_y, 
                    led_g_b=led_g_b, 
                    led_white=led_white
                )
            except Exception as e:
                print(f"設定エラー: {e}")
                return False


# シングルトンインスタンス
patlite = PatliteController() 