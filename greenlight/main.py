"""
GreenLight/greenlight/main.py
Copyright (c) 2025 David Katzin, Wageningen Research Foundation
SPDX-License-Identifier: BSD-3-Clause-Clear
https://github.com/davkat1/GreenLight

First point of entry to the GreenLight package. Opens a GUI dialog box which allows to simply run a standard simulation.
In order to run meaningful simulations, input data must first be acquired. See docs/input_data.md

Next, for information on running more elaborate simulations, see docs.
"""

import argparse
import json
import os

from . import GreenLight, convert_energy_plus
from ._user_interface import MainPrompt
# greenlight/main.py

# 新規追加
from . import output_utils

def main() -> None:
    parser = argparse.ArgumentParser(description="GreenLight simulation runner")
    parser.add_argument("--show", action="store_true", help="結果をコンソールに表示する(デフォルト)")
    parser.add_argument("--mqtt", action="store_true", help="結果をMQTTでpublishする")
    parser.add_argument("--mqtt-config", type=str, default="config.json",
                        help="MQTT設定ファイル(JSON)のパス。指定がなければ'config.json'を試みる")
    parser.add_argument("--mqtt-host", type=str, help="MQTTブローカのホスト名")
    parser.add_argument("--mqtt-port", type=int, help="MQTTブローカのポート番号", default=1883)
    parser.add_argument("--mqtt-topic", type=str, help="publishするトピック名")
    parser.add_argument("--mqtt-username", type=str, help="MQTT接続のユーザー名")
    parser.add_argument("--mqtt-password", type=str, help="MQTT接続のパスワード")

    # argparse で解析
    args, unknown = parser.parse_known_args()

    # 出力モードを決定
    if args.mqtt and args.show:
        parser.error("--mqtt と --show は同時に指定できません")
    elif args.mqtt:
        mode = "mqtt"
    elif args.show:
        mode = "show"
    else:
        mode = "none"
    # 設定ファイルがあれば読み込む
#    mqtt_settings = {}
#    if args.mqtt_config and os.path.exists(args.mqtt_config):
#        with open(args.mqtt_config, "r", encoding="utf-8") as cfg:
#            mqtt_settings = json.load(cfg)
    # 設定ファイルがあれば読み込む（--mqtt-config が指定されていない場合は既定値 "config.json" を試す）
    mqtt_settings = {}
    config_path = args.mqtt_config
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as cfg:
                mqtt_settings = json.load(cfg)
        except Exception as e:
            print(f"設定ファイル {config_path} の読み込み中にエラーが発生しました: {e}")

    # 個別のコマンドライン引数で上書き
    if args.mqtt_host:
        mqtt_settings["host"] = args.mqtt_host
    if args.mqtt_port:
        mqtt_settings["port"] = args.mqtt_port
    if args.mqtt_topic:
        mqtt_settings["topic"] = args.mqtt_topic
    if args.mqtt_username:
        mqtt_settings["username"] = args.mqtt_username
    if args.mqtt_password:
        mqtt_settings["password"] = args.mqtt_password

    # モードと設定を適用
    output_utils.configure(mode=mode, mqtt_settings=mqtt_settings)

    # 以降は従来の処理(MainPromptの起動等)
    # ...

    # Open a UI interface and collect inputs from user
    file_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(file_dir, "..", "models")
    prompt = MainPrompt(models_dir)
    prompt.mainloop()

    if prompt.result:

        # Set up the required input_prompt for GreenLight
        base_path = prompt.result["base_path"]

        sim_length = (prompt.result["end_date"] - prompt.result["start_date"]).total_seconds()

        model = os.path.relpath(prompt.result["model"], base_path)

        mods = []
        if prompt.result["input_data"].endswith(".csv"):
            # An input data file was chosen, use it with the input dates to create a weather input file
            output_path, _ = os.path.splitext(prompt.result["output_file"])
            output_dir, output_file = os.path.split(prompt.result["output_file"])
            input_data_path = os.path.join(output_dir, "..", "input_data")
            filename, _ = os.path.splitext(output_file)
            formatted_weather_file = os.path.abspath(os.path.join(input_data_path, filename + "_formatted_weather.csv"))
            weather_path = convert_energy_plus(
                prompt.result["input_data"],
                formatted_weather_file,
                prompt.result["start_date"],
                prompt.result["end_date"],
                output_format="katzin2021",
            )
            mods = [os.path.relpath(weather_path, base_path)]

        mods.append({"options": {"t_end": sim_length}})
        mods.append(prompt.result["mods"])

        output = os.path.relpath(prompt.result["output_file"], base_path)

        # Create the model instance
        mdl = GreenLight(base_path=base_path, input_prompt=[model, mods], output_path=output)

        # Load, solve, and save. Note: these 3 lines can be replaced by mdl.run()
        mdl.load()
        mdl.solve()
        mdl.save()


if __name__ == "__main__":
    main()
