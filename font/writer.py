# writer.py Implements the Writer class.
# Handles colour, word wrap and tab stops

# V0.5.0 Sep 2021 Color now requires firmware >= 1.17.
# V0.4.3 Aug 2021 Support for fast blit to color displays (PR7682).
# V0.4.0 Jan 2021 Improved handling of word wrap and line clip. Upside-down
# rendering no longer supported: delegate to device driver.
# V0.3.5 Sept 2020 Fast rendering option for color displays

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2019-2021 Peter Hinch

# A Writer supports rendering text to a Display instance in a given font.
# Multiple Writer instances may be created, each rendering a font to the
# same Display object.

# Timings were run on a pyboard D SF6W comparing slow and fast rendering
# and averaging over multiple characters. Proportional fonts were used.
# 20 pixel high font, timings were 5.44ms/467μs, gain 11.7 (freesans20).
# 10 pixel high font, timings were 1.76ms/396μs, gain 4.36 (arial10).

import framebuf

__version__ = (0, 5, 0)

fast_mode = True  # Does nothing. Kept to avoid breaking code.


class Display(framebuf.FrameBuffer):
    def __init__(self, buffer, width, height, mode):
        self.buffer = buffer
        self.width = width
        self.height = height
        self.mode = mode
        super().__init__(self.buffer, self.width, self.height, self.mode)

    def show(self):
        ...


class DisplayState():
    def __init__(self):
        self.text_row = 0
        self.text_col = 0


def _get_id(device):
    if not isinstance(device, framebuf.FrameBuffer):
        raise ValueError('Device must be derived from FrameBuffer.')
    return id(device)

# Basic Writer class for monochrome displays


class Writer():

    state = {}  # Holds a display state for each device
    fontSize = 0

    @staticmethod
    def set_textpos(device: Display, row=None, col=None):
        devid = _get_id(device)
        if devid not in Writer.state:
            Writer.state[devid] = DisplayState()
        s = Writer.state[devid]  # Current state
        if row is not None:
            if row < 0 or row >= device.height:
                raise ValueError('row is out of range')
            s.text_row = row
        if col is not None:
            if col < 0 or col >= device.width:
                raise ValueError('col is out of range')
            s.text_col = col
        return s.text_row,  s.text_col

    def __init__(self, device: Display, fontFamily: str, verbose=True):
        self.devid = _get_id(device)
        self.device = device
        if self.devid not in Writer.state:
            Writer.state[self.devid] = DisplayState()
        self.fontFamily = fontFamily
        self._change_font_size(24)
        if self.font.height() >= device.height or self.font.max_width() >= device.width:
            raise ValueError('Font too large for screen')
        # Allow to work with reverse or normal font mapping
        if self.font.hmap():
            self.map = framebuf.MONO_HMSB if self.font.reverse() else framebuf.MONO_HLSB
        else:
            raise ValueError('Font must be horizontally mapped.')
        if verbose:
            fstr = 'Orientation: Horizontal. Reversal: {}. Width: {}. Height: {}.'
            print(fstr.format(self.font.reverse(), device.width, device.height))
            print('Start row = {} col = {}'.format(
                self._getstate().text_row, self._getstate().text_col))
        self.screenwidth = device.width  # In pixels
        self.screenheight = device.height
        self.bgcolor = 0  # Monochrome background and foreground colors
        self.fgcolor = 1
        self.row_clip = False  # Clip or scroll when screen fullt
        self.col_clip = False  # Clip or new line when row is full
        self.wrap = True  # Word wrap
        self.cpos = 0
        self.tab = 4

        self.glyph = None  # Current char
        self.char_height = 0
        self.char_width = 0
        self.clip_width = 0

    def _change_font_size(self, size: int, bold=False):
        if(self.fontSize == size):
            return
        self.fontSize = size
        fontfile = 'font.'+self.fontFamily+'.'+str(size)
        if(bold):
            fontfile = fontfile+'b'
        self.font = __import__(fontfile, globals(), locals(), [], 0)

    def _getstate(self) -> DisplayState:
        return Writer.state[self.devid]

    def _newline(self):
        s = self._getstate()
        height = self.font.height()
        s.text_row += height
        s.text_col = 0
        margin = self.screenheight - (s.text_row + height)
        y = self.screenheight + margin
        if margin < 0:
            if not self.row_clip:
                self.device.scroll(0, margin)
                self.device.fill_rect(
                    0, y, self.screenwidth, abs(margin), self.bgcolor)
                s.text_row += margin

    def set_clip(self, row_clip=None, col_clip=None, wrap=None):
        if row_clip is not None:
            self.row_clip = row_clip
        if col_clip is not None:
            self.col_clip = col_clip
        if wrap is not None:
            self.wrap = wrap
        return self.row_clip, self.col_clip, self.wrap

    @property
    def height(self):  # Property for consistency with device
        return self.font.height()

    def text(self, text: str, x: int, y: int, fontSize=24, bold=False):
        self._change_font_size(fontSize, bold)
        s = self._getstate()
        s.text_col = x
        s.text_row = y
        self.printstring(text)

    def printstring(self, string, invert=False):
        # word wrapping. Assumes words separated by single space.
        q = string.split('\n')
        last = len(q) - 1
        for n, s in enumerate(q):
            if s:
                self._printline(s, invert)
            if n != last:
                self._printchar('\n')

    def _printline(self, string, invert):
        rstr = None
        # Length > self.screenwidth
        if self.wrap and self.stringlen(string, True):
            pos = 0
            lstr = string[:]
            while self.stringlen(lstr, True):  # Length > self.screenwidth
                pos = lstr.rfind(' ')
                lstr = lstr[:pos].rstrip()
            if pos > 0:
                rstr = string[pos + 1:]
                string = lstr

        for char in string:
            self._printchar(char, invert)
        if rstr is not None:
            self._printchar('\n')
            self._printline(rstr, invert)  # Recurse

    def stringlen(self, string, oh=False):
        if not len(string):
            return 0
        sc = self._getstate().text_col  # Start column
        wd = self.screenwidth
        l = 0
        for char in string[:-1]:
            _, _, char_width = self.font.get_ch(char)
            l += char_width
            if oh and l + sc > wd:
                return True  # All done. Save time.
        char = string[-1]
        _, _, char_width = self.font.get_ch(char)
        if oh and l + sc + char_width > wd:
            l += self._truelen(char)  # Last char might have blank cols on RHS
        else:
            l += char_width  # Public method. Return same value as old code.
        return l + sc > wd if oh else l

    # Return the printable width of a glyph less any blank columns on RHS
    def _truelen(self, char):
        glyph, ht, wd = self.font.get_ch(char)
        div, mod = divmod(wd, 8)
        gbytes = div + 1 if mod else div  # No. of bytes per row of glyph
        mc = 0  # Max non-blank column
        data = glyph[(wd - 1) // 8]  # Last byte of row 0
        for row in range(ht):  # Glyph row
            for col in range(wd - 1, -1, -1):  # Glyph column
                gbyte, gbit = divmod(col, 8)
                if gbit == 0:  # Next glyph byte
                    data = glyph[row * gbytes + gbyte]
                if col <= mc:
                    break
                if data & (1 << (7 - gbit)):  # Pixel is lit (1)
                    mc = col  # Eventually gives rightmost lit pixel
                    break
            if mc + 1 == wd:
                break  # All done: no trailing space
        # print('Truelen', char, wd, mc + 1)  # TEST
        return mc + 1

    def _get_char(self, char, recurse):
        if not recurse:  # Handle tabs
            if char == '\n':
                self.cpos = 0
            elif char == '\t':
                nspaces = self.tab - (self.cpos % self.tab)
                if nspaces == 0:
                    nspaces = self.tab
                while nspaces:
                    nspaces -= 1
                    self._printchar(' ', recurse=True)
                self.glyph = None  # All done
                return

        self.glyph = None  # Assume all done
        if char == '\n':
            self._newline()
            return
        glyph, char_height, char_width = self.font.get_ch(char)
        s = self._getstate()
        np = None  # Allow restriction on printable columns
        if s.text_row + char_height > self.screenheight:
            if self.row_clip:
                return
            self._newline()
        oh = s.text_col + char_width - self.screenwidth  # Overhang (+ve)
        if oh > 0:
            if self.col_clip or self.wrap:
                np = char_width - oh  # No. of printable columns
                if np <= 0:
                    return
            else:
                self._newline()
        self.glyph = glyph
        self.char_height = char_height
        self.char_width = char_width
        self.clip_width = char_width if np is None else np

    # Method using blitting. Efficient rendering for monochrome displays.
    # Tested on SSD1306. Invert is for black-on-white rendering.
    def _printchar(self, char, invert=False, recurse=False):
        s = self._getstate()
        self._get_char(char, recurse)
        if self.glyph is None:
            return  # All done
        buf = bytearray(self.glyph)
        if invert:
            for i, v in enumerate(buf):
                buf[i] = 0xFF & ~ v
        fbc = framebuf.FrameBuffer(
            buf, self.clip_width, self.char_height, self.map)
        self.device.blit(fbc, s.text_col, s.text_row, 0x00)
        s.text_col += self.char_width
        self.cpos += 1

    def tabsize(self, value=None):
        if value is not None:
            self.tab = value
        return self.tab

    def setcolor(self, *_):
        return self.fgcolor, self.bgcolor
