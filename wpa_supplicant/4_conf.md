# 基本配置项

[wpa_supplicant.conf 的配置说明文件](https://zhuanlan.zhihu.com/p/674052171)

# 配置文件示例

```conf
# 请不要修改下面这一行内容，否则将不能正常工作
ctrl_interface=/var/run/wpa_supplicant

# 确保只有root用户能读取WPA的配置
ctrl_interface_group=0

# 使用wpa_supplicant来扫描和选择AP
ap_scan=1

#允许覆盖配置文件；
update_config=1

# 网络1：WPA-PSk密码验证方式，PSK是ASCII密码短语，所有合法的加密方式都允许连接
network={
  ssid="simple"
  psk="very secret passphrase"

  # 优先级越高，能越早连接成功
  priority=5
}

# 网络2：要求对特定的SSID进行扫描（针对那些拒绝广播SSID的AP）
network={
  ssid="second ssid"
  scan_ssid=1
  psk="very secret passphrase"
  priority=2
}

# 网络3：仅使用WPA-PSK方式。允许使用任何合法的加密方式的组合
network={
  ssid="example"
  proto=WPA
  key_mgmt=WPA-PSK
  pairwise=CCMP TKIP
  group=CCMP TKIP WEP104 WEP40
  psk=06b4be19da289f475aa46a33cb793029d4ab3db7a23ee92382eb0106c72ac7bb
  priority=2
}

# 网络4：明文连接方式（不使用WPA和IEEE802.1X）
network={
  ssid="plaintext-test"
  key_mgmt=NONE
}

# 网络5：共享WEP密钥连接方式（不使用WPA和IEEE802.1X）
network={
  ssid="static-wep-test"
  key_mgmt=NONE

  # 引号包含的密钥是ASCII密钥
  wep_key0="abcde"

  # 没有引号包含的密钥是十六进制密钥
  wep_key1=0102030405

  wep_key2="1234567890123"
  wep_tx_keyidx=0
  priority=5
}

# 网络6：共享WEP密钥连接方式（无WPA和IEEE802.1X），使用共享密钥IEEE802.11验证方式
network={
  ssid="static-wep-test2"
  key_mgmt=NONE
  wep_key0="abcde"
  wep_key1=0102030405
  wep_key2="1234567890123"
  wep_tx_keyidx=0
  priority=5
  auth_alg=SHARED
}

# 网络7：在IBSS/ad-hoc网络中使用WPA-None/TKIP
network={
  ssid="test adhoc"
  mode=1
  proto=WPA
  key_mgmt=WPA-NONE
  pairwise=NONE
  group=TKIP
  psk="secret passphrase"
}


#网络8：具有TKIP的WPA-Personal（PSK）和用于频繁PTK密钥更新的强制执行
network={
	ssid="example"
	proto=WPA
	key_mgmt=WPA-PSK
	pairwise=TKIP
	group=TKIP
	psk="not so secure passphrase"
	wpa_ptk_rekey=600
}

#网络9： 仅使用WPA-EAP。 CCMP和TKIP都被接受。 使用WEP104或WEP40作为组密码的AP将不被接受。
network={
	ssid="example"
	proto=RSN
	key_mgmt=WPA-EAP
	pairwise=CCMP TKIP
	group=CCMP TKIP
	eap=TLS
	identity="user@example.com"
	ca_cert="/etc/cert/ca.pem"
	client_cert="/etc/cert/user.pem"
	private_key="/etc/cert/user.prv"
	private_key_passwd="password"
	priority=1
}

#网络10：使用新peaplabel的RADIUS服务器的＃EAP-PEAP / MSCHAPv2配置
network={
	ssid="example"
	key_mgmt=WPA-EAP
	eap=PEAP
	identity="user@example.com"
	password="foobar"
	ca_cert="/etc/cert/ca.pem"
	phase1="peaplabel=1"
	phase2="auth=MSCHAPV2"
	priority=10
}

#网络11：EAP-TTLS / EAP-MD5-具有匿名身份的挑战配置，用于未加密的使用。 仅在加密的TLS隧道内发送实际身份。
network={
	ssid="example"
	key_mgmt=WPA-EAP
	eap=TTLS
	identity="user@example.com"
	anonymous_identity="anonymous@example.com"
	password="foobar"
	ca_cert="/etc/cert/ca.pem"
	priority=2
}

#网络12：EAP-TTLS / MSCHAPv2配置，具有未加密使用的匿名标识。 仅在加密的TLS隧道内发送实际身份。
network={
	ssid="example"
	key_mgmt=WPA-EAP
	eap=TTLS
	identity="user@example.com"
	anonymous_identity="anonymous@example.com"
	password="foobar"
	ca_cert="/etc/cert/ca.pem"
	phase2="auth=MSCHAPV2"
}

#网络13：WPA-EAP，EAP-TTLS，具有用于外部和内部身份验证的不同CA证书。
network={
	ssid="example"
	key_mgmt=WPA-EAP
	eap=TTLS
	# Phase1 / outer authentication
	anonymous_identity="anonymous@example.com"
	ca_cert="/etc/cert/ca.pem"
	# Phase 2 / inner authentication
	phase2="autheap=TLS"
	ca_cert2="/etc/cert/ca2.pem"
	client_cert2="/etc/cer/user.pem"
	private_key2="/etc/cer/user.prv"
	private_key2_passwd="password"
	priority=2
}

#网络14：PWA-PSK和WPA-EAP都被接受。 只有CCMP被接受为成对和组密码。
network={
	ssid="example"
	bssid=00:11:22:33:44:55
	proto=WPA RSN
	key_mgmt=WPA-PSK WPA-EAP
	pairwise=CCMP
	group=CCMP
	psk=06b4be19da289f475aa46a33cb793029d4ab3db7a23ee92382eb0106c72ac7bb
}


#网络15：IEEE 802.1X / EAPOL，使用EAP-TLS动态生成WEP密钥（即无WPA）进行身份验证和密钥生成; 需要单播和广播WEP密钥。
network={
	ssid="1x-test"
	key_mgmt=IEEE8021X
	eap=TLS
	identity="user@example.com"
	ca_cert="/etc/cert/ca.pem"
	client_cert="/etc/cert/user.pem"
	private_key="/etc/cert/user.prv"
	private_key_passwd="password"
	eapol_flags=3
}


#网络16：LEAP与动态WEP密钥
network={
	ssid="leap-example"
	key_mgmt=IEEE8021X
	eap=LEAP
	identity="user"
	password="foobar"
}

#网络17：EAP-IKEv2使用共享机密进行服务器和对等身份验证
network={
	ssid="ikev2-example"
	key_mgmt=WPA-EAP
	eap=IKEV2
	identity="user"
	password="foobar"
}

##网络18： EAP-FAST with WPA (WPA or WPA2)
network={
	ssid="eap-fast-test"
	key_mgmt=WPA-EAP
	eap=FAST
	anonymous_identity="FAST-000102030405"
	identity="username"
	password="password"
	phase1="fast_provisioning=1"
	pac_file="/etc/wpa_supplicant.eap-fast-pac"
}


network={
	ssid="eap-fast-test"
	key_mgmt=WPA-EAP
	eap=FAST
	anonymous_identity="FAST-000102030405"
	identity="username"
	password="password"
	phase1="fast_provisioning=1"
	pac_file="blob://eap-fast-pac"
}



#网络19：具有WPA-None / TKIP的IBSS / ad-hoc网络（已弃用）
network={
	ssid="test adhoc"
	mode=1
	frequency=2412
	proto=WPA
	key_mgmt=WPA-NONE
	pairwise=NONE
	group=TKIP
	psk="secret passphrase"
}

#网络20： 开放式网状网络
network={
	ssid="test mesh"
	mode=5
	frequency=2437
	key_mgmt=NONE
}

#网络21：安全（SAE + AMPE）网络
network={
	ssid="secure mesh"
	mode=5
	frequency=2437
	key_mgmt=SAE
	psk="very secret passphrase"
}


#网络22：捕获允许或多或少所有配置模式的所有示例
network={
	ssid="example"
	scan_ssid=1
	key_mgmt=WPA-EAP WPA-PSK IEEE8021X NONE
	pairwise=CCMP TKIP
	group=CCMP TKIP WEP104 WEP40
	psk="very secret passphrase"
	eap=TTLS PEAP TLS
	identity="user@example.com"
	password="foobar"
	ca_cert="/etc/cert/ca.pem"
	client_cert="/etc/cert/user.pem"
	private_key="/etc/cert/user.prv"
	private_key_passwd="password"
	phase1="peaplabel=0"
}

#网络23：示例配置显示如何使用内联blob作为CA证书数据而不是使用外部文件
network={
	ssid="example"
	key_mgmt=WPA-EAP
	eap=TTLS
	identity="user@example.com"
	anonymous_identity="anonymous@example.com"
	password="foobar"
	ca_cert="blob://exampleblob"
	priority=20
}

blob-base64-exampleblob={
SGVsbG8gV29ybGQhCg==
}

#网络24：示例配置将两个AP列入黑名单 - 这些将被忽略对于这个网络。
network={
	ssid="example"
	psk="very secret passphrase"
	bssid_blacklist=02:11:22:33:44:55 02:22:aa:44:55:66
}

#网络25：示例配置将AP选择限制为一组特定的AP;任何其他与掩码地址不匹配的AP都将被忽略。
network={
	ssid="example"
	psk="very secret passphrase"
	bssid_whitelist=02:55:ae:bc:00:00/ff:ff:ff:ff:00:00 00:00:77:66:55:44/00:00:ff:ff:ff:ff
}

#网络26：示例配置文件仅在通道36上扫描。
freq_list=5180
network={
	key_mgmt=NONE
}


#网络27：示例MACsec配置
network={
	key_mgmt=IEEE8021X
	eap=TTLS
	phase2="auth=PAP"
	anonymous_identity="anonymous@example.com"
	identity="user@example.com"
	password="secretr"
	ca_cert="/etc/cert/ca.pem"
	eapol_flags=0
	macsec_policy=1
}
```
