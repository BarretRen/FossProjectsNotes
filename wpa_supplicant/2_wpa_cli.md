wpa_supplicant 是一个连接、配置 WiFi 的工具，它主要包含 wpa_supplicant 与 wpa_cli 两个程序。 可以通过 wpa_cli 来进行 WiFi 的配置与连接,前提要保证 wpa_supplicant 正常启动。

## 常用命令

| 命令                                          | 作用                               |
| --------------------------------------------- | ---------------------------------- |
| wpa_cli help                                  | 打印帮助信息                       |
| wpa_cli -i wlan0 status                       | 显示当前连接信息                   |
| wpa_cli -i wlan0 scan                         | 搜索周围 WiFi 信息                 |
| wpa_cli -i wlan0 scan_result                  | 显示上一次的搜索结果               |
| wpa_cli -i wlan0 list_networks                | 显示已配置的网络与信息             |
| wpa_cli -i wlan0 add_network                  | 添加一个网络返回一个数字 n         |
| wpa_cli -i wlan0 set_network n ssid "name"    | 输入要连接的 WiFi 名称             |
| wpa_cli -i wlan0 set_network n key_mgmt NONE  | 输入加密方式 OPEN/WEP              |
| wpa_cli -i wlan0 set_network n wep_key0 "psk" | 输入加密方式 WEP 的密码            |
| wpa_cli -i wlan0 set_network n psk "psk"      | 输入加密方式 WPA/WPA2 的密码       |
| wpa_cli -i wlan0 enable_network n             | 设置后需要启用 WiFi                |
| wpa_cli -i wlan0 save_config                  | 保存 WiFi 配置                     |
| wpa_cli -i wlan0 select_network n             | 有多个 WiFi 时选择其中一个         |
| wpa_cli -i wlan0 reconfigure                  | 重新加载配置文件                   |
| wpa_cli -i wlan0 disconnect                   | 断开 WiFi 连接                     |
| wpa_cli -i wlan0 reconnect                    | 重新连接                           |
| wpa_cli -i wlan0 remove_network n             | 移除 WiFi 配置                     |
| wpa_cli -i wlan0 terminate                    | 关闭后台服务器程序                 |
| wpa_cli [-i wlan0]                            | 进入交互模式, 命令可以为 status 等 |
