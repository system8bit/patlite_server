from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from enum import Enum
from typing import Optional, List
import asyncio

from app.patlite_controller import patlite, PatliteColor, PatlitePattern, LED

app = FastAPI(
    title="パトライト制御API",
    description="hidapiを使用してパトライトデバイスを制御するAPI",
    version="1.0.0"
)

# 非同期処理のためのセマフォ
# これによりパトライト操作は一度に1つのリクエストのみが実行されるようになる
patlite_semaphore = asyncio.Semaphore(1)


class StatusResponse(BaseModel):
    """ステータスレスポンスモデル"""
    success: bool
    message: str


class LightRequest(BaseModel):
    """ライト設定リクエストモデル"""
    color: int  # PatliteColorのenum値
    pattern: int  # PatlitePatternのenum値


class BuzzerRequest(BaseModel):
    """ブザー設定リクエストモデル"""
    sound: int  # ブザー音階
    mode: int   # ブザー動作モード


class LEDRequest(BaseModel):
    """LED設定リクエストモデル"""
    leds: List[str]  # LEDのリスト ("RED", "YELLOW", "GREEN", "BLUE", "WHITE")


class AllSettingsRequest(BaseModel):
    """全ての設定を一度に行うリクエストモデル"""
    leds: List[str]  # LEDのリスト
    buzzer_sound: int  # ブザー音階
    buzzer_mode: int   # ブザー動作モード


class SimpleBuzzerRequest(BaseModel):
    """シンプルなブザー設定リクエストモデル"""
    sound: int = 6  # デフォルトはD7
    mode: int = 3   # デフォルトは3回動作


# パトライト操作用の同期関数（バックグラウンドタスクとして実行）
def sync_patlite_operation(operation_func, *args, **kwargs):
    """
    パトライトを操作する同期関数をバックグラウンドタスクとして実行
    
    Args:
        operation_func: 実行する関数
        args, kwargs: 関数に渡す引数
    
    Returns:
        操作の結果
    """
    return operation_func(*args, **kwargs)


@app.on_event("startup")
async def startup():
    """アプリ起動時にデバイスに接続を試みる"""
    async with patlite_semaphore:
        if not patlite.connected:
            patlite.connect()


@app.on_event("shutdown")
async def shutdown():
    """アプリ終了時にデバイスから切断する"""
    async with patlite_semaphore:
        if patlite.connected:
            patlite.disconnect()


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """接続状態を取得"""
    async with patlite_semaphore:
        return StatusResponse(
            success=patlite.connected,
            message="デバイスに接続されています" if patlite.connected else "デバイスに接続されていません"
        )


@app.post("/connect", response_model=StatusResponse)
async def connect_device():
    """デバイスに接続"""
    async with patlite_semaphore:
        if patlite.connected:
            return StatusResponse(success=True, message="すでに接続されています")
        
        success = patlite.connect()
        if success:
            return StatusResponse(success=True, message="接続に成功しました")
        else:
            raise HTTPException(status_code=500, detail="デバイスへの接続に失敗しました")


@app.post("/disconnect", response_model=StatusResponse)
async def disconnect_device():
    """デバイスから切断"""
    async with patlite_semaphore:
        if not patlite.connected:
            return StatusResponse(success=True, message="既に切断されています")
        
        patlite.disconnect()
        return StatusResponse(success=True, message="切断しました")


@app.post("/light", response_model=StatusResponse)
async def set_light(request: LightRequest, background_tasks: BackgroundTasks):
    """ライトの設定"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        try:
            color = PatliteColor(request.color)
            pattern = PatlitePattern(request.pattern)
        except ValueError:
            raise HTTPException(status_code=400, detail="無効な色またはパターンが指定されました")
        
        # バックグラウンドタスクでパトライト操作を実行
        background_tasks.add_task(sync_patlite_operation, patlite.set_light, color, pattern)
        
        return StatusResponse(success=True, message="ライトを設定しました")


@app.post("/leds", response_model=StatusResponse)
async def set_leds(request: LEDRequest, background_tasks: BackgroundTasks):
    """複数のLEDを同時に設定"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        try:
            led_flags = LED.NONE
            for led_name in request.leds:
                if led_name.upper() == "RED":
                    led_flags |= LED.RED
                elif led_name.upper() == "YELLOW":
                    led_flags |= LED.YELLOW
                elif led_name.upper() == "GREEN":
                    led_flags |= LED.GREEN
                elif led_name.upper() == "BLUE":
                    led_flags |= LED.BLUE
                elif led_name.upper() == "WHITE":
                    led_flags |= LED.WHITE
                else:
                    raise ValueError(f"無効なLED名: {led_name}")
            
            # バックグラウンドタスクでパトライト操作を実行
            background_tasks.add_task(sync_patlite_operation, patlite.set_leds, led_flags)
            
            return StatusResponse(success=True, message="LEDを設定しました")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.post("/buzzer", response_model=StatusResponse)
async def set_buzzer(request: BuzzerRequest, background_tasks: BackgroundTasks):
    """ブザーの設定"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        # バックグラウンドタスクでパトライト操作を実行
        background_tasks.add_task(sync_patlite_operation, patlite.set_buzzer, request.sound, request.mode)
        
        return StatusResponse(success=True, message="ブザーを設定しました")


@app.post("/buzzer/stop", response_model=StatusResponse)
async def stop_buzzer(background_tasks: BackgroundTasks):
    """ブザーの停止"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        # バックグラウンドタスクでパトライト操作を実行
        background_tasks.add_task(sync_patlite_operation, patlite.stop_buzzer)
        
        return StatusResponse(success=True, message="ブザーを停止しました")


@app.post("/all", response_model=StatusResponse)
async def set_all(request: AllSettingsRequest, background_tasks: BackgroundTasks):
    """全ての設定を一度に行う"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        try:
            led_flags = LED.NONE
            for led_name in request.leds:
                if led_name.upper() == "RED":
                    led_flags |= LED.RED
                elif led_name.upper() == "YELLOW":
                    led_flags |= LED.YELLOW
                elif led_name.upper() == "GREEN":
                    led_flags |= LED.GREEN
                elif led_name.upper() == "BLUE":
                    led_flags |= LED.BLUE
                elif led_name.upper() == "WHITE":
                    led_flags |= LED.WHITE
                else:
                    raise ValueError(f"無効なLED名: {led_name}")
            
            # バックグラウンドタスクでパトライト操作を実行
            background_tasks.add_task(
                sync_patlite_operation, 
                patlite.set_all, 
                led_flags, 
                request.buzzer_sound, 
                request.buzzer_mode
            )
            
            return StatusResponse(success=True, message="すべての設定を適用しました")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.post("/reset", response_model=StatusResponse)
async def reset_lights(background_tasks: BackgroundTasks):
    """全てのライトをオフにする"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        # バックグラウンドタスクでパトライト操作を実行
        background_tasks.add_task(sync_patlite_operation, patlite.reset)
        
        return StatusResponse(success=True, message="ライトをリセットしました")


# 簡易操作用APIエンドポイント

@app.post("/turn_on_red", response_model=StatusResponse)
async def turn_on_red(background_tasks: BackgroundTasks):
    """赤色LEDを点灯させる"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        # バックグラウンドタスクでパトライト操作を実行
        background_tasks.add_task(sync_patlite_operation, patlite.set_leds, LED.RED)
        
        return StatusResponse(success=True, message="赤色LEDを点灯しました")


@app.post("/turn_on_yellow", response_model=StatusResponse)
async def turn_on_yellow(background_tasks: BackgroundTasks):
    """黄色LEDを点灯させる"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        # バックグラウンドタスクでパトライト操作を実行
        background_tasks.add_task(sync_patlite_operation, patlite.set_leds, LED.YELLOW)
        
        return StatusResponse(success=True, message="黄色LEDを点灯しました")


@app.post("/turn_on_green", response_model=StatusResponse)
async def turn_on_green(background_tasks: BackgroundTasks):
    """緑色LEDを点灯させる"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        # バックグラウンドタスクでパトライト操作を実行
        background_tasks.add_task(sync_patlite_operation, patlite.set_leds, LED.GREEN)
        
        return StatusResponse(success=True, message="緑色LEDを点灯しました")


@app.post("/turn_off_LED", response_model=StatusResponse)
async def turn_off_LED(background_tasks: BackgroundTasks):
    """すべてのLEDを消灯させる"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        # バックグラウンドタスクでパトライト操作を実行
        background_tasks.add_task(sync_patlite_operation, patlite.set_leds, LED.NONE)
        
        return StatusResponse(success=True, message="すべてのLEDを消灯しました")


@app.post("/play_buzzer", response_model=StatusResponse)
async def play_buzzer(background_tasks: BackgroundTasks, request: SimpleBuzzerRequest = None):
    """ブザーを鳴らす（デフォルトはD7音で3回鳴動）"""
    async with patlite_semaphore:
        if not patlite.connected:
            raise HTTPException(status_code=400, detail="デバイスに接続されていません")
        
        if request is None:
            request = SimpleBuzzerRequest()
        
        # バックグラウンドタスクでパトライト操作を実行
        background_tasks.add_task(sync_patlite_operation, patlite.set_buzzer, request.sound, request.mode)
        
        return StatusResponse(success=True, message="ブザーを鳴らしました") 