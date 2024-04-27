import time
from micropython import const
from machine import Pin
import machine

# I2C ADDRESS
_CST816_ADDR = const(0x15)

# Register Addresses
_CST816_GestureID = const(0x01)
_CST816_FingerNum = const(0x02)
_CST816_XposH = const(0x03)
_CST816_XposL = const(0x04)
_CST816_YposH = const(0x05)
_CST816_YposL = const(0x06)

_CST816_ChipID = const(0xA7)
_CST816_ProjID = const(0xA8)
_CST816_FwVersion = const(0xA9)
_CST816_MotionMask = const(0xAA)

_CST816_BPC0H = const(0xB0)
_CST816_BPC0L = const(0xB1)
_CST816_BPC1H = const(0xB2)
_CST816_BPC1L = const(0xB3)

_CST816_IrqPluseWidth = const(0xED)
_CST816_NorScanPer = const(0xEE)
_CST816_MotionSlAngle = const(0xEF)
_CST816_LpScanRaw1H = const(0xF0)
_CST816_LpScanRaw1L = const(0xF1)
_CST816_LpScanRaw2H = const(0xF2)
_CST816_LpScanRaw2L = const(0xF3)
_CST816_LpAutoWakeTime = const(0xF4)
_CST816_LpScanTH = const(0xF5)
_CST816_LpScanWin = const(0xF6)
_CST816_LpScanFreq = const(0xF7)
_CST816_LpScanIdac = const(0xF8)
_CST816_AutoSleepTime = const(0xF9)
_CST816_IrqCtl = const(0xFA)
_CST816_AutoReset = const(0xFB)
_CST816_LongPressTime = const(0xFC)
_CST816_IOCtl = const(0xFD)
_CST816_DisAutoSleep = const(0xFE)

# Modes
_CST816_Point_Mode = const(1)
_CST816_Gesture_Mode = const(2)
_CST816_ALL_Mode = const(3)

# Gestures
_CST816_Gesture_None = const(0)
_CST816_Gesture_Up = const(1)
_CST816_Gesture_Down = const(2)
_CST816_Gesture_Left = const(3)
_CST816_Gesture_Right = const(4)
_CST816_Gesture_Click = const(5)
_CST816_Gesture_Double_Click = const(11)
_CST816_Gesture_Long_Press = const(12)
_CST816_Gesture_translate = {
    90: {
        _CST816_Gesture_Up: _CST816_Gesture_Right,
        _CST816_Gesture_Down: _CST816_Gesture_Left,
        _CST816_Gesture_Left: _CST816_Gesture_Up,
        _CST816_Gesture_Right: _CST816_Gesture_Down,
    },
    180: {
        _CST816_Gesture_Up: _CST816_Gesture_Down,
        _CST816_Gesture_Down: _CST816_Gesture_Up,
        _CST816_Gesture_Left: _CST816_Gesture_Right,
        _CST816_Gesture_Right: _CST816_Gesture_Left,
    },
    270: {
        _CST816_Gesture_Up: _CST816_Gesture_Right,
        _CST816_Gesture_Down: _CST816_Gesture_Left,
        _CST816_Gesture_Left: _CST816_Gesture_Up,
        _CST816_Gesture_Right: _CST816_Gesture_Down,
    }
}

_CST816_Gesture_map = {
    _CST816_Gesture_None:'NONE',
    _CST816_Gesture_Up:'SWIPE UP',
    _CST816_Gesture_Down:'SWIPE DOWN',
    _CST816_Gesture_Left: 'SWIPE LEFT',
    _CST816_Gesture_Right: 'SWIPE RIGHT',
    _CST816_Gesture_Click: 'SINGLE CLICK',
    _CST816_Gesture_Double_Click: 'DOUBLE CLICK',
    _CST816_Gesture_Long_Press: 'LONG PRESS',
}


class CST816:
    """Driver for the CST816 Touchscreen connected over I2C."""

    def __init__(self, i2c_bus, irq=None, addr=_CST816_ADDR, rotation=0):
        self._i2c_bus = i2c_bus
        self._i2c_addr = addr
        self._rotation = rotation
        
        self.gesture_id = None
        self.num_fingers = None
        self.x = 0
        self.y = 0
        
        self.mode = _CST816_ALL_Mode
        self._event_available = False
        
        self._irq_pin = irq
        self._attach_handler()

    def _i2c_write(self, reg, value):
        """Write to I2C"""
        self._i2c_bus.writeto_mem(self._i2c_addr, reg, bytes([value]))

    def _i2c_read(self, reg, length=1):
        """Read from I2C"""
        data = bytearray(length)
        self._i2c_bus.readfrom_mem_into(self._i2c_addr, reg, data)
        return data[0] if length == 1 else data

    def _attach_handler(self):
        if self._irq_pin:
            self._irq_pin.irq(handler=self._irq_handler, trigger=Pin.IRQ_FALLING)

    def _disable_handler(self):
        if self._irq_pin:
            self._irq_pin.irq(handler=None)

    def _irq_handler(self, pin):
        state = machine.disable_irq()
        
        self._event_available = True

        machine.enable_irq(state)
        
        # debounce, only accept one touch every 200ms
        #self._disable_handler()
        #time.sleep_ms(200)
        #self._attach_handler()

    def _translate_coordinate(self, x, y):
        if self._rotation == 0:
            return x, y
        elif self._rotation == 90:
            return 240-y, x
        elif self._rotation == 180:
            return 240-x, 240-y
        elif self._rotation == 270:
            return y, 240-x
        
        raise Exception(f'Unknown rotation value {self._rotation}')

    def _translate_gesture_id(self, gesture_id):
        if self._rotation in _CST816_Gesture_translate:
            return _CST816_Gesture_translate[self._rotation].get(gesture_id, gesture_id)
        
        return gesture_id

    def _read_touch(self):
        data_raw = self._i2c_read(_CST816_GestureID, length=6)
        
        self.gesture_id = self._translate_gesture_id(data_raw[0])
        self.num_fingers = data_raw[1]
        x = ((data_raw[2] & 0x0F) << 8) + data_raw[3]
        y = ((data_raw[4] & 0x0F) << 8) + data_raw[5]
        
        self.x, self.y = self._translate_coordinate(x, y)
        
    def available(self):
        if (self._event_available):
            self._read_touch()
            self._event_available = False
            return self.gesture_id != _CST816_Gesture_None
        return False

    def get_gesture(self):
        return _CST816_Gesture_map.get(self.gesture_id, 'UNKNOWN')

    def who_am_i(self):
        """Check the Chip ID"""
        return bool(self._i2c_read(_CST816_ChipID) == 0xB5)

    def reset(self):
        """Make the Chip Reset"""
        self._i2c_write(_CST816_DisAutoSleep, 0x00)
        time.sleep(0.1)
        self._i2c_write(_CST816_DisAutoSleep, 0x01)
        time.sleep(0.1)

    def read_revision(self):
        """Read Firmware Version"""
        return self._i2c_read(_CST816_FwVersion)

    def wake_up(self):
        """Make the Chip Wake Up"""
        self._i2c_write(_CST816_DisAutoSleep, 0x00)
        time.sleep(0.01)
        self._i2c_write(_CST816_DisAutoSleep, 0x01)
        time.sleep(0.05)
        self._i2c_write(_CST816_DisAutoSleep, 0x01)

    def stop_sleep(self):
        """Make the Chip Stop Sleeping"""
        self._i2c_write(_CST816_DisAutoSleep, 0x01)

    def set_mode(self, mode):
        """Set the Behaviour Mode"""
        if mode == _CST816_Point_Mode:
            self._i2c_write(_CST816_IrqCtl, 0x41)
        elif mode == _CST816_Gesture_Mode:
            self._i2c_write(_CST816_IrqCtl, 0x11)
            self._i2c_write(_CST816_MotionMask, 0x01)
        else:
            self._i2c_write(_CST816_IrqCtl, 0x71)
        self.mode = mode

