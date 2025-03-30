from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from typing import Optional, List

from app.patlite_controller import patlite, PatliteColor, PatlitePattern, LED

app = FastAPI(
    title="パトライト制御API",
    description="hidapiを使用してパトライトデバイスを制御するAPI",
    version="1.0.0"
)


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


@app.on_event("startup")
async def startup():
    """アプリ起動時にデバイスに接続を試みる"""
    if not patlite.connected:
        patlite.connect()


@app.on_event("shutdown")
async def shutdown():
    """アプリ終了時にデバイスから切断する"""
    if patlite.connected:
        patlite.disconnect()


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """接続状態を取得"""
    return StatusResponse(
        success=patlite.connected,
        message="デバイスに接続されています" if patlite.connected else "デバイスに接続されていません"
    )


@app.post("/connect", response_model=StatusResponse)
async def connect_device():
    """デバイスに接続"""
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
    if not patlite.connected:
        return StatusResponse(success=True, message="既に切断されています")
    
    patlite.disconnect()
    return StatusResponse(success=True, message="切断しました")


@app.post("/light", response_model=StatusResponse)
async def set_light(request: LightRequest):
    """ライトの設定"""
    if not patlite.connected:
        raise HTTPException(status_code=400, detail="デバイスに接続されていません")
    
    try:
        color = PatliteColor(request.color)
        pattern = PatlitePattern(request.pattern)
    except ValueError:
        raise HTTPException(status_code=400, detail="無効な色またはパターンが指定されました")
    
    success = patlite.set_light(color, pattern)
    if success:
        return StatusResponse(success=True, message="ライトを設定しました")
    else:
        raise HTTPException(status_code=500, detail="ライトの設定に失敗しました")


@app.post("/leds", response_model=StatusResponse)
async def set_leds(request: LEDRequest):
    """複数のLEDを同時に設定"""
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
        
        success = patlite.set_leds(led_flags)
        if success:
            return StatusResponse(success=True, message="LEDを設定しました")
        else:
            raise HTTPException(status_code=500, detail="LEDの設定に失敗しました")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/buzzer", response_model=StatusResponse)
async def set_buzzer(request: BuzzerRequest):
    """ブザーの設定"""
    if not patlite.connected:
        raise HTTPException(status_code=400, detail="デバイスに接続されていません")
    
    success = patlite.set_buzzer(request.sound, request.mode)
    if success:
        return StatusResponse(success=True, message="ブザーを設定しました")
    else:
        raise HTTPException(status_code=500, detail="ブザーの設定に失敗しました")


@app.post("/buzzer/stop", response_model=StatusResponse)
async def stop_buzzer():
    """ブザーの停止"""
    if not patlite.connected:
        raise HTTPException(status_code=400, detail="デバイスに接続されていません")
    
    success = patlite.stop_buzzer()
    if success:
        return StatusResponse(success=True, message="ブザーを停止しました")
    else:
        raise HTTPException(status_code=500, detail="ブザーの停止に失敗しました")


@app.post("/all", response_model=StatusResponse)
async def set_all(request: AllSettingsRequest):
    """全ての設定を一度に行う"""
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
        
        success = patlite.set_all(led_flags, request.buzzer_sound, request.buzzer_mode)
        if success:
            return StatusResponse(success=True, message="すべての設定を適用しました")
        else:
            raise HTTPException(status_code=500, detail="設定の適用に失敗しました")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reset", response_model=StatusResponse)
async def reset_lights():
    """全てのライトをオフにする"""
    if not patlite.connected:
        raise HTTPException(status_code=400, detail="デバイスに接続されていません")
    
    success = patlite.reset()
    if success:
        return StatusResponse(success=True, message="ライトをリセットしました")
    else:
        raise HTTPException(status_code=500, detail="ライトのリセットに失敗しました")


# 簡易操作用APIエンドポイント

@app.post("/turn_on_red", response_model=StatusResponse)
async def turn_on_red():
    """赤色LEDを点灯させる"""
    if not patlite.connected:
        raise HTTPException(status_code=400, detail="デバイスに接続されていません")
    
    success = patlite.set_leds(LED.RED)
    if success:
        return StatusResponse(success=True, message="赤色LEDを点灯しました")
    else:
        raise HTTPException(status_code=500, detail="赤色LEDの点灯に失敗しました")


@app.post("/turn_on_yellow", response_model=StatusResponse)
async def turn_on_yellow():
    """黄色LEDを点灯させる"""
    if not patlite.connected:
        raise HTTPException(status_code=400, detail="デバイスに接続されていません")
    
    success = patlite.set_leds(LED.YELLOW)
    if success:
        return StatusResponse(success=True, message="黄色LEDを点灯しました")
    else:
        raise HTTPException(status_code=500, detail="黄色LEDの点灯に失敗しました")


@app.post("/turn_on_green", response_model=StatusResponse)
async def turn_on_green():
    """緑色LEDを点灯させる"""
    if not patlite.connected:
        raise HTTPException(status_code=400, detail="デバイスに接続されていません")
    
    success = patlite.set_leds(LED.GREEN)
    if success:
        return StatusResponse(success=True, message="緑色LEDを点灯しました")
    else:
        raise HTTPException(status_code=500, detail="緑色LEDの点灯に失敗しました")


@app.post("/turn_off_LED", response_model=StatusResponse)
async def turn_off_LED():
    """すべてのLEDを消灯させる"""
    if not patlite.connected:
        raise HTTPException(status_code=400, detail="デバイスに接続されていません")
    
    success = patlite.set_leds(LED.NONE)
    if success:
        return StatusResponse(success=True, message="すべてのLEDを消灯しました")
    else:
        raise HTTPException(status_code=500, detail="LEDの消灯に失敗しました")


@app.post("/play_buzzer", response_model=StatusResponse)
async def play_buzzer(request: SimpleBuzzerRequest = None):
    """ブザーを鳴らす（デフォルトはD7音で3回鳴動）"""
    if not patlite.connected:
        raise HTTPException(status_code=400, detail="デバイスに接続されていません")
    
    if request is None:
        request = SimpleBuzzerRequest()
    
    success = patlite.set_buzzer(request.sound, request.mode)
    if success:
        return StatusResponse(success=True, message="ブザーを鳴らしました")
    else:
        raise HTTPException(status_code=500, detail="ブザー動作に失敗しました") 