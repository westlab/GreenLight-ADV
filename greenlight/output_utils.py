# greenlight/output_utils.py
"""
出力方式の切り替えと MQTT publish を行うユーティリティ
"""

from typing import Any, Dict, Iterable, Optional

import paho.mqtt.client as mqtt  # ライブラリは requirements に追加しておく

# 出力モード: 'show' ならコンソール表示、'mqtt' ならMQTT publish
# _OUTPUT_MODE: str = "show"

# MQTT設定を格納する辞書。host, port, topic, username, password など
_MQTT_SETTINGS: Dict[str, Any] = {}
_client = None  # paho-mqtt client インスタンス


def configure(mode: str = "none", mqtt_settings: Optional[Dict[str, Any]] = None) -> None:
    """
    出力モードとMQTTの設定を構成する。`mode` が 'mqtt' の場合、MQTTクライアントを初期化して接続する。
    """
    global _OUTPUT_MODE, _MQTT_SETTINGS, _client
    _OUTPUT_MODE = mode
    _MQTT_SETTINGS = mqtt_settings or {}
    if _OUTPUT_MODE == "mqtt":
        host = _MQTT_SETTINGS.get("host", "localhost")
        port = int(_MQTT_SETTINGS.get("port", 1883))
        username = _MQTT_SETTINGS.get("username")
        password = _MQTT_SETTINGS.get("password")
        _client = mqtt.Client()
        if username is not None and password is not None:
            _client.username_pw_set(username, password)
        _client.connect(host, port)
        # 非同期 publish を使う場合は loop_start() を呼び出してもよい
    else:
        # show モードならクライアントは不要
        _client = None


def output_row(row_values: Iterable[Any]) -> None:
    """
    行データを出力する。モードに応じてコンソール表示か MQTT publish を行う。
    """
    # 数値や numpy.float64 などを文字列に変換し、カンマ区切り文字列を生成
    payload = ",".join(str(v) for v in row_values)
    if _OUTPUT_MODE == "mqtt":
        if _client is None:
            raise RuntimeError("MQTT client not configured. call configure(mode='mqtt', ...) first.")
        topic = _MQTT_SETTINGS.get("topic", "greenlight/output")
        # QoS や retain を必要に応じて設定
        _client.publish(topic, payload)
    elif _OUTPUT_MODE == "show":
        # 画面に表示
        print(payload, flush=True)


def get_mode() -> str:
    """現在の出力モードを返す。'show' または 'mqtt'"""
    return _OUTPUT_MODE


def info(message: str) -> None:
    """
    ログや進捗などの情報を表示する。
    show モードのときだけ print() を行い、mqtt モードでは何もしない。
    """
    if _OUTPUT_MODE == "show":
        print(message, flush=True)
