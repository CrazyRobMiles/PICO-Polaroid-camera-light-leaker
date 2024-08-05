import neopixel
from machine import Pin
from picographics import PicoGraphics,DISPLAY_PICO_DISPLAY
import time
from pimoroni import Button
from pimoroni import RGBLED

class DisplayItem:
    LEFT = 0
    CENTRE = 1
    RIGHT = 2

    def __init__(self, x, y, display, foreground, background, font, size, width, height, alignment):
        self.display = display
        self.x = x
        self.y = y
        self.foreground = foreground
        self.background = background
        self.font = font
        self.size = size
        self.width = width
        self.height = height
        self.alignment = alignment
        self.text_width = 0
        self.text_x = 0
        self.old_text = ""

    def do_display(self, text):
        if text == self.old_text:
            return False
        print("Displaying:",text)
        if self.text_width != 0:
            self.display.set_pen(self.background)
            self.display.rectangle(self.text_x, self.y,
                                   self.text_width, self.height)
        self.display.set_pen(self.foreground)
        self.display.set_font(self.font)
        self.text_width = self.display.measure_text(text, scale=self.size)
        if self.alignment == DisplayItem.CENTRE:
            self.text_x = round((self.width-self.text_width)/2)
        elif self.alignment == DisplayItem.LEFT:
            self.text_x = 0
        elif self.alignment == DisplayItem.RIGHT:
            self.text_x = self.x+(self.width-self.text_width)
        self.display.text(text, self.text_x, self.y, scale=self.size)
        self.old_text = text
        return True

class ButtonPins:
    
    button_a = 12
    button_b = 13
    button_x = 14
    button_y = 15
    
class Display:
    DRAW_COL = 15
    ERASE_COL = 0
    FAINT_COL = 2
    DOTTED_COL = 14

    BAR_X = 10
    BAR_Y = 53
    BAR_AREA_WIDTH = 96
    BAR_AREA_HEIGHT = 25

    FONT = "bitmap8"
    FONT_SIZE = 4
    FONT_HEIGHT = 16

    TARIFF_FONT = "bitmap8"
    TARIFF_FONT_SIZE = 4
    TARIFF_FONT_HEIGHT = 32
    MIN_Y = 78
    MAX_Y = 22

    def __init__(self, ctrl, display):
        self.ctrl = ctrl
        self.display = display
        self.width, self.height = self.display.get_bounds()
        self.display.set_pen(self.ERASE_COL)
        self.display.rectangle(0, 0, self.width, self.height)
        half_width = round(self.width/2.0)
        self.status = DisplayItem(0, 3*self.FONT_HEIGHT, self.display, self.DRAW_COL,
                                  self.ERASE_COL, self.FONT, self.FONT_SIZE, self.width, 32, DisplayItem.CENTRE)
        self.button_a = DisplayItem(0, 0, self.display, self.DRAW_COL,
                                  self.ERASE_COL, self.FONT, self.FONT_SIZE, half_width, 32, DisplayItem.LEFT)
        self.button_b = DisplayItem(0, self.height-(self.FONT_HEIGHT*2), self.display, self.DRAW_COL,
                                  self.ERASE_COL, self.FONT, self.FONT_SIZE, half_width, 32, DisplayItem.LEFT)
        self.button_x = DisplayItem(half_width, 0, self.display, self.DRAW_COL,
                                  self.ERASE_COL, self.FONT, self.FONT_SIZE, half_width, 32, DisplayItem.RIGHT)
        self.button_y = DisplayItem(half_width, self.height-(self.FONT_HEIGHT*2), self.display, self.DRAW_COL,
                                  self.ERASE_COL, self.FONT, self.FONT_SIZE, half_width, 32, DisplayItem.RIGHT)
        self.display_dirty = True

    def do_status(self, status):
        if self.status.do_display(status):
            self.display_dirty = True

    def draw(self):
        if self.display_dirty:
            self.display.update()
            self.display_dirty = False

class Col:
    
    RED = (255, 0, 0)
    YELLOW = (255, 150, 0)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    MAGENTA = (255, 0, 255)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREY = (10, 10, 10)
    VIOLET = (127,0,155)
    INDIGO = (75,0,130)
    ORANGE = (255,165,0)
       
    values=(RED, GREEN, BLUE, YELLOW, MAGENTA, CYAN, GREY, WHITE)

class Pixels:
    
    def fill(self,colour,brightness=1):
        r=round(colour[0]*brightness)
        g=round(colour[1]*brightness)
        b=round(colour[2]*brightness)
        for i in self.pixel_range:
            self.pixels[i]=(r,g,b)
        self.pixels.write()
        
    def dot(self,colour,pixel,brightness=1):
        r=round(colour[0]*brightness)
        g=round(colour[1]*brightness)
        b=round(colour[2]*brightness)
        self.pixels[pixel]=(r,g,b)
        self.pixels.write()
        
    def off(self):
        for i in self.pixel_range:
            self.pixels[i]=(0,0,0)
        self.pixels.write()
        
    def __init__(self,pixel_pin,no_of_pixels):
        self.pixel_pin = pixel_pin
        self.no_of_pixels = no_of_pixels
        self.pixels = neopixel.NeoPixel(Pin(self.pixel_pin), self.no_of_pixels)
        self.pixel_range = range(0,self.no_of_pixels)
        self.fill(Col.BLACK)
        
    def update(self):
        pass

    def shutdown(self):
        pass

     
    @staticmethod
    def dim(col):
        return (col[0]/40, col[1]/40, col[2]/40)
    
class PageButton:
    
    def __init__(self,pin, display):
        self.display = display
        self.pin = pin
        self.button = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.state = self.button.value()
        self.text = ""
        self.up = None
        self.down=None
        self.debounce_count=0
        self.debounce_limit=5
        
    def setup(self,text,down,up):
        self.text = text
        self.down = down
        self.up = up

    def update(self):
        newState = self.button.value()
        if newState != self.state:
            if self.debounce_count > self.debounce_limit:
                self.debounce_count = 0
                self.state = newState
                if newState:
                    self.up()
                else:
                    self.down()
            else:
                self.debounce_count = self.debounce_count+1
        return
    
    def draw(self):
        return self.display.do_display(self.text) 
    
class PageOfButtons:
    
    def __init__(self, button_dict):
        self.dict = button_dict
    
    def setup_buttons(self,settings):
        for setting in settings:
            name,text,pressed,released=setting
            button = self.dict[name]
            if button != None:
                button.setup(text,pressed,released)
                
    def update(self):
        for button in self.dict.values():
            button.update()
    
    def draw(self):
        result = False
        for button in self.dict.values():
            if button.draw():
                result = True
        return result
        
class LightLeaker:
            
    def do_col_set_led(self):
        col = Col.values[self.colour_no]
        self.led.set_rgb(col[0],col[1],col[2])
        
    def do_col_next(self):
        self.colour_no = self.colour_no+1
        if self.colour_no >= len(Col.values):
            self.colour_no = 0
        self.do_col_set_led()
        
    def do_col_back(self):
        self.colour_no = self.colour_no-1
        if self.colour_no < 0:
            self.colour_no = len(Col.values)-1
        self.do_col_set_led()
        
    def do_col_done(self):
        self.do_display_main_menu()
   
    def do_col(self):
        self.display.do_status("")

        col_page = [ ("a","Next",self.do_col_next, self.released),
                      ("b","Back",self.do_col_back, self.released),
                      ("x","",self.do_nothing, self.do_nothing),
                      ("y","Done",self.do_col_done, self.released)]
        
        self.buttons.setup_buttons(col_page)
    
    def do_nothing(self):
        pass

    def released(self):
        pass
        
    def do_show_exp(self):
        msg = "Exp:"+str(self.exposure)
        self.display.do_status(msg)
        
    def do_exp_up(self):
        self.exposure = self.exposure + 1
        if self.exposure > self.max_exposure:
            self.exposure = self.min_exposure
        self.do_show_exp()

    def do_exp_down(self):
        self.exposure = self.exposure - 1
        if self.exposure < self.min_exposure:
            self.exposure = self.max_exposure
        self.do_show_exp()

    def do_exp_done(self):
        self.do_display_main_menu()

    def do_exp(self):
        self.do_show_exp()
        exp_page = [ ("a","Up",self.do_exp_up, self.released),
                      ("b","Down",self.do_exp_down, self.released),
                      ("x","",self.do_nothing, self.do_nothing),
                      ("y","Done",self.do_exp_done, self.released)]
        
        self.buttons.setup_buttons(exp_page)
        
    patterns = ["fill","leak"]

    def do_show_pattern(self):
        msg = self.patterns[self.pattern]
        self.display.do_status(msg)
        
    def do_pattern_up(self):
        self.pattern = self.pattern + 1
        if self.pattern >= len(self.patterns):
            self.pattern = 0
        self.do_show_pattern()

    def do_pattern_down(self):
        self.pattern = self.pattern - 1
        if self.pattern < 0:
            self.pattern = len(self.patterns)-1
        self.do_show_pattern()

    def do_pattern_done(self):
        self.do_display_main_menu()

    def do_pattern(self):
        self.do_show_pattern()
        pattern_page = [ ("a","Up",self.do_pattern_up, self.released),
                      ("b","Down",self.do_pattern_down, self.released),
                      ("x","",self.do_nothing, self.do_nothing),
                      ("y","Done",self.do_pattern_done, self.released)]
        
        self.buttons.setup_buttons(pattern_page)

    def do_go(self):
        go_page = [ ("a","",self.do_nothing, self.released),
                      ("b","",self.do_nothing, self.released),
                      ("x","",self.do_nothing, self.do_nothing),
                      ("y","",self.do_nothing, self.released)]

        self.buttons.setup_buttons(go_page)
        
        self.display.do_status("Exposing!")
        self.display.draw()
        if self.patterns[self.pattern]=="fill":
            print("  fill")
            self.pixels.fill(Col.values[self.colour_no],0.01)
        elif self.patterns[self.pattern]:
            print("  leak")
            self.pixels.dot(Col.values[self.colour_no],5,0.01)
        time.sleep_ms(self.exposure)
        self.pixels.off()
        
        self.do_display_main_menu()
    
    def do_display_main_menu(self):
        
        self.display.do_status("LightLeaker")
        
        main_page = [ ("a","Patt",self.do_pattern, self.released),
                      ("b","Col",self.do_col, self.released),
                      ("x","Exp",self.do_exp, self.released),
                      ("y","GO",self.do_go, self.released)]
        
        self.buttons.setup_buttons(main_page)
    
    def __init__(self,display, pixel_pin,no_of_pixels):
        self.display = Display(self, display)
        self.colour_no = 0
        self.min_exposure = 1
        self.max_exposure = 10
        self.exposure = self.min_exposure
        self.min_pattern = 1
        self.max_pattern = 10
        self.pattern = self.min_pattern 
        self.pixels = Pixels(pixel_pin, no_of_pixels)
        self.led = RGBLED(6, 7, 8)
        self.do_col_set_led()
        
        self.buttons = PageOfButtons({
            "a":PageButton(12,self.display.button_a),
            "b":PageButton(13,self.display.button_b),
            "x":PageButton(14,self.display.button_x),
            "y":PageButton(15,self.display.button_y)
            })
        
        self.do_display_main_menu()
        
    def update(self):
        self.buttons.update()
    
    def draw(self):
        if self.buttons.draw():
            self.display.display_dirty = True
        self.display.draw()

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY, rotate=0)
lightLeaker = LightLeaker(display, pixel_pin=10, no_of_pixels=15)

while True:
   lightLeaker.update()
   lightLeaker.draw()


