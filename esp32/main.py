from machine import Pin, SoftI2C as I2C, ADC
import time
import cst816
import setup
import vga2_16x16
import vga2_16x32
import vga2_8x16
import vga2_8x8
import vga2_bold_16x16
import vga2_bold_16x32
import gc9a01
import random
import math
import settings
import socket
import machine
import esp32
import framebuf
import network
import requests

fonts = {
    '8x8': vga2_8x8,
    '8x16': vga2_8x16,
    '16x16': vga2_16x16,
    '16x16b': vga2_bold_16x16,
    '16x32': vga2_16x32,
    '16x32b': vga2_bold_16x32,
}

LEFT_BUTTON = 'up'
RIGHT_BUTTON = 'down'

T = time.time()
battery_level = ADC(Pin(1),atten=ADC.ATTN_6DB)

settings.load()

def triangle(tft, x, y, size, up=True):
    multiplier = -1 if up else 1
    for i in range(size//2):
        tft.hline(x+i, y+i*multiplier, size-(2*i), gc9a01.YELLOW)

def text_center(tft, font, text, c, b, x=None, y=None):
    if x is None:
        x = (240 - font.WIDTH*len(text)) // 2
    else:
        x = x - (font.WIDTH*len(text) // 2)
        
    if y is None:
        y = (240 - font.HEIGHT) // 2
    else:
        y = y - (font.HEIGHT // 2)
    
    tft.text(font, text, x, y, c, b)

class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', 80))
        self.sock.listen(5)
        self.handlers = {}
        
    def register(self, method, path, handler):
        self.handlers.setdefault(method, {})
        self.handlers[method][path] = handler
        
    def handle(self):
        try:
            res = self.sock.accept()
        except OSError:
            return
        
        conn, addr = res
        
        method, path, query_args, headers, data = parse_request(conn)
      
        print (f'Request {method} {path} {query_args}')        
        try:
            response = self.handlers[method][path](method, path, query_args, headers, data)
        except KeyError:
            response = 'Not Found'
        
        conn.send(response)
        conn.close()
        
    def shutdown(self):
        self.sock.close()
        self.sock = None

class App:
    def __init__(self, tft, fonts):
        self.tft = tft
        self.fonts = fonts
        self.screen_classes = {}
        self.stack = []
        self.force_changes = False
        
    def register(self, name, cls):
        if name in self.screen_classes:
            raise Exception(f'Screen {name} has already been registered: {self.screen_classes[name]}.')
        
        if not issubclass(cls, Screen):
            raise Exception(f'Class {cls} should be a subclass of Screen')
        
        self.screen_classes[name] = cls

    def push(self, name, **kwargs):
        if name not in self.screen_classes:
            raise Exception(f'Unknown screen {name}')
        
        cls = self.screen_classes[name]
        self.tft.fill(0)
        self.stack.append(cls(self, **kwargs))
        self.force_changes = True
        
    def pop(self):
        if len(self.stack) > 1:
            screen = self.stack.pop(-1)
            screen.loop()
            screen.deinit()
            self.tft.fill(0)
            self.force_changes = True
    
    def draw(self):
        self.force_changes = False
        
        if self.stack:
            self.stack[-1].draw()
        else:
            self.tft.fill(gc9a01.BLACK)
            text_center(self.tft, self.fonts['8x16'], 'No Screen Configured', gc9a01.WHITE, gc9a01.BLACK)

    def handle_button(self, i):
        print('!! HANDLE BUTTON', time.ticks_ms())
        if self.stack:
            self.stack[-1].handle_button(i)
        
    def handle_click(self, x, y):
        if self.stack:
            self.stack[-1].handle_click(x, y)
            
    def has_changes(self):
        if self.force_changes:
            return True
        
        if self.stack:
            return self.stack[-1].has_changes()
    
        return False
    
    def loop(self):
        if self.stack:
            self.stack[-1].loop()
    
class Screen:
    def __init__(self, app):
        self.app = app
        self.pending_changes = False
    
    def draw(self):
        raise NotImplementedError()
    
    def handle_click(self, x, y):
        raise NotImplementedError()
    
    def handle_button(self, i):
        raise NotImplementedError()
    
    def has_changes(self):
        return self.pending_changes
    
    def loop(self):
        pass
    
    def deinit(self):
        pass

class MenuItem:
    def __init__(self, name, details=None):
        self.name = name
        self.details = details
        
    def __str__(self):
        return self.name

class Menu(Screen):
    def __init__(self, app, name, items):
        super().__init__(app)
        self.name = name
        self.items = [MenuItem(self.name)] + items + [MenuItem('')]
        self.start_index = 0
        self.row_heights = [70, 100, 70]
        self.row_dirty = [None, None, None]
        
    def _draw_one_row(self, index, row):
        item = self.items[index]
        text = item.name
        details = item.details

        y = sum(self.row_heights[:row])
                
        font = self.app.fonts['16x32b'] if row > 0 and row < len(self.row_heights)-1 else self.app.fonts['8x16']
        if font.WIDTH*len(text) > 240:
            font = self.app.fonts['8x16']
        color = gc9a01.WHITE if row > 0 and row < len(self.row_heights)-1 else gc9a01.CYAN
        background_color = gc9a01.BLUE if index == 0 else gc9a01.BLACK
        
        self.app.tft.fill_rect(0, y+1 if y > 0 else 0, 240, self.row_heights[row]-1, background_color)

        self.app.tft.text(
                    font,
                    text,
                    (240-font.WIDTH*len(text)) // 2,
                    y + (self.row_heights[row] - font.HEIGHT) // 2,
                    color, background_color)
        
        if row == 1 and details:
            self.app.tft.text(
                    self.app.fonts['8x16'],
                    details,
                    (240-self.app.fonts['8x16'].WIDTH*len(details)) // 2,
                    y + self.app.fonts['16x32b'].HEIGHT + (self.row_heights[row] - self.app.fonts['8x16'].HEIGHT) // 2,
                    color, gc9a01.BLUE if index == 0 else gc9a01.BLACK)
            
        if row < 2:
            self.app.tft.hline(0, y+self.row_heights[row], 240, gc9a01.WHITE)

    def draw(self):
        self.pending_changes = False

        for i, text in enumerate(self.items[self.start_index:self.start_index+3]):
            self._draw_one_row(self.start_index+i, i)
            
        if self.start_index > 0:
            triangle(self.app.tft, 112, 15, 16, up=True)
        
        if self.start_index < len(self.items) - 3:
            triangle(self.app.tft, 112, 225, 16, up=False)
        else:
            self.app.tft.fill_rect(112, 225, 16, 8, gc9a01.BLACK)


    def handle_click(self, x, y):
        if y < self.row_heights[0]:
            self.handle_button(LEFT_BUTTON)
        elif 240 - y < self.row_heights[-1]:
            self.handle_button(RIGHT_BUTTON)
        else:   
            self.handle_selection(self.start_index, self.items[self.start_index+1])
    
    def handle_button(self, i):    
        if i == RIGHT_BUTTON:
            if self.start_index < len(self.items) - 3:
                self.start_index += 1
                self.pending_changes = True
        elif i == LEFT_BUTTON:
            if self.start_index > 0:
                self.start_index -= 1
                self.pending_changes = True
            
    def handle_selection(self, i, item):
        print('SELECTION MADE', i, item)
        
class MainMenu(Menu):
    def __init__(self, app):
        name = 'Main Menu'
        items = [MenuItem('Pending Games'), MenuItem('Games'), MenuItem('Ended Games'), MenuItem('Timer'), MenuItem('Settings'), MenuItem('System')]
        super().__init__(app, name, items)

    def handle_selection(self, i, item):
        if item.name == 'Pending Games':
            self.app.push('games_menu', menu_name='Pending Games', status='not-started')
        elif item.name == 'Games':
            self.app.push('games_menu', menu_name='Games', status='in-progress')
        elif item.name == 'Ended Games':
            self.app.push('games_menu', menu_name='Ended Games', status='ended')
        elif item.name == 'Settings':
            self.app.push('settings_menu')
        elif item.name == 'Timer':
            self.app.push('timer')
        elif item.name == 'System':
            self.app.push('system_menu')
        
            
class GamesMenu(Menu):
    def __init__(self, app, menu_name=None, status=None):
        items = [MenuItem('Loading...')]
        super().__init__(app, menu_name, items)
        self.status = status
        
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.wlan.connect(settings.get('NETWORK_SSID'), settings.get('NETWORK_PASSWORD'))
        self.loading = True
        self.error = False
        
        self.headers = {
            'Authorization':'Bearer ' + settings.get('BEARER_TOKEN', default='MISSING'),
            'accept': 'application/json'
        }
        
        self.events = []

    def handle_selection(self, i, item):
        if item.name == 'Create Event':
            self.start_index = 0
            data = {'season': 2024}
            r = requests.post("http://score-keeper.duckdns.org:8080/api/event", json=data, headers=self.headers)
            d = r.json()
            print('!! HERE', d)
            r.close()
            
            self.loading = True
            self.pending_changes = True
        else:
            self.app.push('score_board', event=self.events[i])
 
    def draw(self):
        if not self.loading and not self.error:
            self.items = [self.items[0], self.items[-1]]
            for event in self.events:
                item = MenuItem(event['name'])
                item.details = f"{event['away_score']} - {event['home_score']} [P{event['period']}]"
                self.items.insert(-1, item)
        
            if self.status == 'not-started':
                self.items.insert(-1, MenuItem('Create Event'))
        super().draw()
 
    def loop(self):
        if self.wlan.isconnected():
            if self.loading:
                try:
                    t = time.time()
                    r = requests.get(f'http://score-keeper.duckdns.org:8080/api/event?sort=datetime__period__created_at&pp=10&p=1&resolves=home_team%2Caway_team&status={self.status}', headers=self.headers)
                    data = r.json()
                    r.close()
                    
                    print('!! TT', time.time() - t)
                    
                    self.events = data['events']
                    
                    for event in self.events:
                        event['name'] = f"{event['away_team_name']} vs {event['home_team_name']}"

                    self.loading = False
                    self.pending_changes = True
                    print('!! TOTAL', time.time() - t)
                except OSError as e:
                    print('ERROR:', e)
                    self.items[1].name = 'FAILED'
                    self.items[1].details = 'Something happened....'
                    self.loading = False
                    self.error = True
                    self.pending_changes = True
                
    def deinit(self):
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self.wlan.active(False)

class ScoreBoard(Screen):
    def __init__(self, app, event=None):
        super().__init__(app)
        self.event = event
        
        self.headers = {
            'Authorization':'Bearer ' + settings.get('BEARER_TOKEN', default='MISSING'),
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        self.pending_data = []
        
    def draw(self):
        self.pending_changes = False

        self.app.tft.fill_rect(112, 225, 16, 8, gc9a01.BLACK)
        text_center(self.app.tft, self.app.fonts['16x32b'], f"{self.event['away_score']:02}", gc9a01.RED, gc9a01.BLACK, x=60, y=75)
        text_center(self.app.tft, self.app.fonts['8x16'], self.event['away_team_name'], gc9a01.RED, gc9a01.BLACK, x=60, y=120)

        text_center(self.app.tft, self.app.fonts['16x32b'], f"{self.event['home_score']:02}", gc9a01.BLUE, gc9a01.BLACK, x=180, y=75)
        text_center(self.app.tft, self.app.fonts['8x16'], self.event['home_team_name'], gc9a01.BLUE, gc9a01.BLACK, x=180, y=120)

        text_center(self.app.tft, self.app.fonts['8x16'], self.event['verbose_status'], gc9a01.YELLOW, gc9a01.BLACK, x=120, y=35)
        text_center(self.app.tft, self.app.fonts['8x16'], f"Period {self.event['period']}", gc9a01.YELLOW, gc9a01.BLACK, x=120, y=150)

        self.app.tft.hline(0, 170, 240, gc9a01.WHITE)
        font = self.app.fonts['8x16']
        if self.event['status'] == 'not-started':
            text = 'Start Event'
        elif self.event['status'] == 'in-progress':
            text = 'End Event'
        elif self.event['status'] == 'ended':
            text = 'Restart Event'
        row_height = 70
        y = 170
        self.app.tft.text(
                    font,
                    text,
                    (240-font.WIDTH*len(text)) // 2,
                    y + (row_height - font.HEIGHT) // 2,
                    gc9a01.WHITE, gc9a01.BLACK)

    def handle_button(self, i):
        if self.event['status'] == 'in-progress':
            delta = 1
            if i == LEFT_BUTTON:
                self.event['away_score'] += delta
                self.pending_data.append(('score', {'away_delta': delta, 'away_score': self.event['away_score'], 'home_score': self.event['home_score']}))
                self.pending_changes = True
            elif i == RIGHT_BUTTON:
                self.event['home_score'] += delta
                self.pending_data.append(('score', {'home_delta': delta, 'away_score': self.event['away_score'], 'home_score': self.event['home_score']}))
                self.pending_changes = True

    def loop(self):
        if self.pending_data:
            data = self.pending_data
            self.pending_data = []
            
            for t, d in data:
                print('!!', t,d)
                r = None
                if t == 'score':
                    r = requests.post(f"http://score-keeper.duckdns.org:8080/api/event/{self.event['id']}/score", json=d, headers=self.headers)
                elif t == 'update':
                    r = requests.patch(f"http://score-keeper.duckdns.org:8080/api/event/{self.event['id']}", json=d, headers=self.headers)

                if r:
                    d = r.json()
                    r.close()
    
    def handle_click(self, x, y):
        if y > 170:
            def callback():
                if self.event['status'] == 'not-started':
                    self.event['status'] = 'in-progress'
                    self.pending_data.append(('update', {'status': 'in-progress'}))
                elif self.event['status'] == 'in-progress':
                    self.event['status'] = 'ended'
                    self.pending_data.append(('update', {'status': 'ended'}))
                elif self.event['status'] == 'ended':
                    self.event['status'] = 'in-progress'
                    self.pending_data.append(('update', {'status': 'in-progress'}))
            self.app.push('confirm_menu', message='Are you sure?', callback=callback)

class SystemMenu(Menu):
    def __init__(self, app):
        name = 'System'
        items = [MenuItem('Battery'), MenuItem('Restart'), MenuItem('Power Off')]
        super().__init__(app, name, items)
        self.last_update = None
        
    def handle_selection(self, i, item):
        if item.name == 'Power Off':
            def callback():
                esp32.wake_on_ext0(Pin(21, Pin.IN, Pin.PULL_DOWN), level=esp32.WAKEUP_ANY_HIGH)
                machine.deepsleep()
            self.app.push('confirm_menu', message='Are you sure?', callback=callback)
        elif item.name == 'Restart':
            machine.reset()
            
    def loop(self):
        level1 = 3*battery_level.read_uv()/943800
        if self.start_index == 0 and (self.last_update is None or time.time() - self.last_update > 1):
            self.items[1].details = f'{level1:.2f}V'
            self.last_update = time.time()
            self.pending_changes = True
    

class SettingsMenu(Menu):
    def __init__(self, app):
        name = "ConnectToMe"
        items = [MenuItem('Initializing'), MenuItem('Cancel')]
        super().__init__(app, name, items)
        
        
        self.ap = network.WLAN(network.AP_IF)
        print('!! XX', self.ap.status(), self.ap.active())
        self.ap.active(True)
        self.ap.config(ssid="ConnectToMe") 
        self.ap.active(True)
        
        self.server = Server()
        self.server.register('GET', '/', web_page)
        self.server.register('POST', '/', handle_settings)
        
        self.was_active = False
        
    def loop(self):
        if self.ap.active():
            if not self.was_active:
                self.pending_changes = True
                self.was_active = True
                self.items[1].name = self.ap.ifconfig()[0]
            
            self.server.handle()
        
    def handle_selection(self, i, item):
        if item.name == 'Cancel':
            self.app.pop()
            
    def deinit(self):
        super().deinit()
        print('DEINIT CALLED')
        self.server.shutdown()
        self.ap.active(False)

class ConfirmMenu(Menu):
    def __init__(self, app, message=None, callback=None):
        name = message
        items = [MenuItem('Yes'), MenuItem('No')]
        super().__init__(app, name, items)
        
        self.callback = callback
        
    def handle_selection(self, i, item):
        if item.name == 'Yes':
            self.app.pop()
            if self.callback:
                self.callback()
        elif item.name == 'No':
            self.app.pop()

class Timer(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.start_time = time.time()
        self.last_update = time.time()
        
    def has_changes(self):
        if super().has_changes():
            return True
        
        if time.time() - self.last_update >= 1:
            return True
        
        return False
    
    def draw(self):
        self.last_update = time.time()
        minutes, seconds = divmod(time.time() - self.start_time, 60)
        clock_str = f"{minutes:02d}:{seconds:02d}"
        text_center(self.app.tft, self.app.fonts['16x32'], clock_str, gc9a01.WHITE, gc9a01.BLACK)

    def handle_click(self, x, y):
        pass

def web_page(method, path, query_args, headers, data):
    ssid = settings.get('NETWORK_SSID', '')
    password = settings.get('NETWORK_PASSWORD', '')
    bearer_token = settings.get('BEARER_TOKEN', '')
    
    html = f"""<html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1"/>
        </head>
        <body>
            <h1>Settings</h1>
            <form method="POST">
                <div>
                    <label>Network SSID
                        <input type="text" name="network_ssid" value="{ssid}"/>
                    </label>
                </div>
                <div>
                    <label>Network Password
                        <input type="password" name="network_password" value="{password}"/>
                    </label>
                </div>
                <div>
                    <label>Bearer Token
                        <input type="text" name="bearer_token" value="{bearer_token}"/>
                    </label>
                </div>
                <button type="submit">Save</button>
            </form>
        </body>
    </html>"""
    return html

def handle_settings(method, path, query_args, headers, data):
    settings.set('NETWORK_SSID', data['network_ssid'])
    settings.set('NETWORK_PASSWORD', data['network_password'])
    settings.set('BEARER_TOKEN', data['bearer_token'])
    settings.save()

    new_location = '/'
    return ("HTTP/1.1 302 Found\r\nLocation: {}\r\n".format(new_location)).encode()

_hextobyte_cache = None

def unquote(string):
    """unquote('abc%20def') -> 'abc def'."""
    global _hextobyte_cache

    # Note: strings are encoded as UTF-8. This is only an issue if it contains
    # unescaped non-ASCII characters, which URIs should not.
    if not string:
        return ''

    bits = string.split('%')
    if len(bits) == 1:
        return string

    res = [bits[0]]
    append = res.append

    # Build cache for hex to char mapping on-the-fly only for codes
    # that are actually used
    if _hextobyte_cache is None:
        _hextobyte_cache = {}

    for item in bits[1:]:
        try:
            code = item[:2]
            char = _hextobyte_cache.get(code)
            if char is None:
                char = _hextobyte_cache[code] = bytes([int(code, 16)])
            append(char)
            append(item[2:])
        except KeyError:
            append('%')
            append(item)

    return ''.join(res)

def parse_request(conn):
    request = conn.recv(1024)
    method, url, data = request.split(b' ', 2)
    
    method = method.upper().decode()
    url = url.decode()
    
    url_split = url.split('?',1)
    if len(url_split) == 1:
        path = url
        query_args = {}
    else:
        path = url_split[0]
        query_args = {y[0]: unquote(y[1]) if len(y) > 1 else None for y in [x.split('=', 1) for x in url_split[1].split('&')]}
    
    data_split = data.split(b'\r\n\r\n')
    data_split[0] = data_split[0].decode()
    
    headers = {y[0].strip(): y[1].strip() if len(y) > 1 else None for y in [x.split(':', 1) for x in data_split[0].split('\r\n')]}
    
    data = b''
    if len(data_split) > 1:
        data = data_split[1]
        
    try:
        content_length = int(headers.get('Content-Length'))
    except TypeError:
        content_length = None
        
    while content_length and len(data) < content_length:
        data += conn.recv(1024)
    
    data = data.decode().replace('+', ' ')
    print('!! HERE', data)
    data = {y[0]: unquote(y[1]) if len(y) > 1 else None for y in [x.split('=', 1) for x in data.split('&')]}
    
    print('!! DATA', data)
    return method, path, query_args, headers, data


class Keypad:
    DEBOUNCE_DELAY = 1000
    
    def __init__(self, key_map):
        self.buttons = {}
        self.key_map = key_map
        self.last_press_time = 0
        self.keys_pressed = []

        for pin_id, name in self.key_map.items():
            button = Pin(pin_id, Pin.IN, Pin.PULL_DOWN)
            self.buttons[button] = pin_id
            button.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.button_handler)

    def button_handler(self, pin):
        current_time = time.ticks_ms()
        if current_time-self.last_press_time > self.DEBOUNCE_DELAY:
            self.last_press_time = current_time
            pin_id = self.buttons[pin]
            self.keys_pressed.append(self.key_map[pin_id])

    def pop(self):
        if self.keys_pressed:
            return self.keys_pressed.pop(0)
        return None

def main():
    key_map = {18: 'up', 21: 'down'}
    keypad = Keypad(key_map)
      
    idle_since = time.time()
    sleep = False
    
    # this order of initialization is important or else
    # the touch screen continually triggers events
    i2c = I2C(sda=Pin(6), scl=Pin(7))
    tft = setup.init_screen(rotation=2)
    tft.fill(0)
    touch = cst816.CST816(i2c, irq=Pin(5, Pin.IN, Pin.PULL_DOWN), rotation=180)

    a = App(tft, fonts)
    a.register('confirm_menu', ConfirmMenu)
    a.register('games_menu', GamesMenu)
    a.register('main_menu', MainMenu)
    a.register('score_board', ScoreBoard)
    a.register('settings_menu', SettingsMenu)
    a.register('system_menu', SystemMenu)
    a.register('timer', Timer)
    a.push('main_menu')
    a.draw()

    while True:
        if touch.available():
            print(
                "Position: {0},{1} - Gesture: {2} - Pressed? {3}".format(
                    touch.x,
                    touch.y,
                    touch.get_gesture(),
                    touch.num_fingers
                )
            )
            
            idle_since = time.time()
            if sleep:
                tft.on()
                sleep = False
                continue
            
            if touch.num_fingers == 0:
                if touch.get_gesture() == 'SINGLE CLICK':
                    a.handle_click(touch.x, touch.y)
                elif touch.get_gesture() == 'SWIPE RIGHT':
                    a.pop()
        else:
            key_pressed = keypad.pop()
            if key_pressed:
               a.handle_button(key_pressed)

        if a.has_changes():
            idle_since = time.time()
            print('redrawing')
            a.draw()
            
        a.loop()
        
        if time.time() - idle_since > 10:
            tft.off()
            sleep = True
        
        time.sleep(0.01)
   
try:
    main()
except Exception as e:
    print('EXCEPTION', e)
    machine.reset()
