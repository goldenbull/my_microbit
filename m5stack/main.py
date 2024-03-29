from m5stack import *
import network, json, machine, time
from micropython import const
import deviceCfg
from menu import wifi
import ntptime

wlan_sta = network.WLAN(network.STA_IF)
wlan_ap = network.WLAN(network.AP_IF)

_connect_ssid = "cheater"
_connect_pwd = "3.1415926535897932"
_connect_timeout_time = 5

CONNECT_TIMEOUT = const(0)
CONNECTING = const(1)
CONNECTED = const(2)
WAIT_CONNECT = const(4)


def is_connected():
    return wlan_sta.isconnected()


def connect_update():
    global _connect_timeout_time

    if wlan_sta.isconnected():
        deviceCfg.save_wifi(_connect_ssid, _connect_pwd)
        return CONNECTED

    now_time = time.ticks_ms()
    if _connect_timeout_time == 0:
        return WAIT_CONNECT

    if _connect_timeout_time > now_time:
        return CONNECTING
    else:
        if wlan_sta.active():
            wlan_sta.disconnect()
            wlan_sta.active(False)
        _connect_timeout_time = 0
        return CONNECT_TIMEOUT


def connect(ssid, pwd, timeout, block=False):
    global _connect_ssid, _connect_pwd, _connect_timeout_time
    if wlan_sta.isconnected() and _connect_ssid == ssid and pwd == _connect_pwd:
        return True
    if wlan_sta.isconnected():
        wlan_sta.disconnect()
        time.sleep_ms(100)
    wlan_sta.active(True)
    wlan_sta.connect(ssid, pwd)
    _connect_ssid = ssid
    _connect_pwd = pwd
    _connect_timeout_time = time.ticks_ms() + timeout

    if block:
        while True:
            state = connect_update()
            if state == CONNECT_TIMEOUT:
                return False
            elif state == CONNECTED:
                return True
            time.sleep_ms(50)


def reconnect():
    if _connect_ssid != None:
        connect(_connect_ssid, _connect_pwd, 10000, True)


def disconnect():
    wlan_sta.disconnect()


def connect_ui(ssid, pwd):
    from menu import wifi
    menu = wifi.WifiMenu()
    menu.init(ssid)
    connect(ssid, pwd, 10000)
    connect_fail = False
    result = 0
    while True:
        state = connect_update()
        if state == CONNECT_TIMEOUT:
            menu.set_state(wifi.CONNECT_FAIL)
            connect_fail = True
        elif state == CONNECTED:
            result = 0
            break

        if connect_fail and btnB.wasPressed():
            menu.set_state(wifi.CONNECT)
            connect_fail = False
            connect(ssid, pwd, 10000)
        if btnC.wasPressed():
            result = 1
            break

        menu.update()
        time.sleep_ms(20)

    menu.deinit()
    return result


def refreshUI():
    lcd.clear()

    # battery
    lcd.print("battery level:" + str(power.getBatteryLevel()), 10, 10)
    lcd.print("isCharging:" + str(power.isCharging()), 10, 30)
    lcd.print("isFull:" + str(power.isChargeFull()), 10, 50)

    # wifi
    lcd.print('WIFI connected:' + str(is_connected()), 10, 80)

    # time
    ntp = ntptime.client("cn.pool.ntp.org", 8)
    ntp.updateTime()
    lcd.print(ntp.formatDatetime(), 20, 150)


brightness = 1
reconnect()
lcd.setBrightness(brightness)
refreshUI()


def inc_brightness():
    global brightness
    brightness += 1
    if brightness > 20:
        brightness = 20
    lcd.setBrightness(brightness)

def dec_brightness():
    global brightness
    brightness -= 1
    if brightness < 1:
        brightness = 1
    lcd.setBrightness(brightness)

while True:
    if btnA.wasPressed():
        dec_brightness()
    if btnB.wasPressed():
        inc_brightness()
    if btnC.wasPressed():
        refreshUI()
    time.sleep(0.1)
