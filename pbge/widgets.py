import frects
from . import my_state,render_text,draw_text,TEXT_COLOR,Border,default_border
import pygame
import image
import rpgmenu

# respond_event: Receives an event.
#   If the widget has a method corresponding to the event,
#   that method will be called.

# Note that the widget needs to be added to my_state.widgets to be used!
# Or, as the child of another widget. Removing it from that list
# removes it.

ACTIVE_FLASH = [(0,0,0),] * 5 + [(230,230,0),] * 20

widget_border_off = Border( border_width=8, tex_width=16, border_name="sys_widbor_edge1.png", tex_name="sys_widbor_back.png", tl=0, tr=3, bl=4, br=5, t=1, b=1, l=2, r=2, padding=2 )
widget_border_on = Border( border_width=8, tex_width=16, border_name="sys_widbor_edge2.png", tex_name="sys_widbor_back.png", tl=0, tr=3, bl=4, br=5, t=1, b=1, l=2, r=2, padding=2 )
popup_menu_border = Border( border_width=8, tex_width=16, border_name="sys_widbor_edge2.png", tex_name="sys_defbackground.png", tl=0, tr=3, bl=4, br=5, t=1, b=1, l=2, r=2, padding=8, transparent=False )



class Widget( frects.Frect ):
    def __init__( self, dx, dy, w, h, data=None, on_click=None, tooltip=None, children=(), active=True, **kwargs ):
        # on_click takes widget, event as parameters.
        super(Widget, self).__init__(dx,dy,w,h,**kwargs)
        self.data = data
        self.active = active
        self.tooltip = tooltip
        self.on_click = on_click
        self.children = list(children)
    def respond_event( self, ev ):
        if self.active:
            for c in self.children:
                c.respond_event(ev)
            if self.get_rect().collidepoint(pygame.mouse.get_pos()):
                if self.is_kb_selectable() and (ev.type == pygame.MOUSEBUTTONUP) and (ev.button == 1) and not my_state.widget_clicked:
                    if not my_state.widget_clicked:
                        my_state.active_widget = self
                    if self.on_click:
                        self.on_click(self,ev)
                    my_state.widget_clicked = True
            elif my_state.active_widget is self:
                if self.on_click and (ev.type == pygame.KEYDOWN) and (ev.key in my_state.get_keys_for("click_widget")):
                    self.on_click(self,ev)
                    my_state.widget_clicked = True
            self._builtin_responder(ev)

    def _builtin_responder(self,ev):
        pass

    def super_render( self ):
        # This renders the widget and children, setting tooltip and whatnot.
        if self.active:
            self.render()
            if self is my_state.active_widget:
                self.flash_when_active()
            if self.tooltip and self.get_rect().collidepoint(pygame.mouse.get_pos()):
                my_state.widget_tooltip = self.tooltip
            for c in self.children:
                c.super_render()
    def flash_when_active(self):
        if my_state.active_widget_hilight:
            pygame.draw.rect(my_state.screen, ACTIVE_FLASH[my_state.anim_phase % len(ACTIVE_FLASH)], self.get_rect(), 1)
    def render( self ):
        pass
    def is_kb_selectable(self):
        return self.on_click

class ButtonWidget( Widget ):
    def __init__( self, dx, dy, w, h, sprite=None, frame=0, on_frame=0, off_frame=0, **kwargs ):
        super(ButtonWidget, self).__init__(dx,dy,w,h,**kwargs)
        self.sprite = sprite
        self.frame = frame
        self.on_frame = on_frame
        self.off_frame = off_frame
    def render( self ):
        if self.sprite:
            self.sprite.render(self.get_rect(),self.frame)

class LabelWidget( Widget ):
    def __init__( self, dx, dy, w, h, text='***', color=None, font=None, justify=-1, draw_border=False, border=widget_border_off, text_fun = None, **kwargs ):
        # text_fun is a function that takes this widget as a parameter. It returns the text to display.
        super(LabelWidget, self).__init__(dx,dy,w,h,**kwargs)
        self.text = text
        self.color = color or TEXT_COLOR
        self.font = font or my_state.small_font
        self.justify = justify
        self.draw_border = draw_border
        self.border = border
        self.text_fun = text_fun
    def render( self ):
        if self.draw_border:
            self.border.render(self.get_rect())
        if self.text_fun:
            self.text = self.text_fun(self)
        draw_text(self.font,self.text,self.get_rect(),self.color,self.justify)

class TextEntryWidget( Widget ):
    ALLOWABLE_CHARACTERS = u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 1234567890()-=_+,.?"'
    def __init__( self, dx, dy, w, h, text='***', color=None, font=None, justify=-1, **kwargs ):
        super(TextEntryWidget, self).__init__(dx,dy,w,h,**kwargs)
        self.char_list = list(text)
        self.color = color or TEXT_COLOR
        self.font = font or my_state.big_font
        self.justify = justify
        self.input_cursor = image.Image( "sys_textcursor.png" , 8 , 16 )

    def render( self ):
        mydest = self.get_rect()
        if self is my_state.active_widget:
            widget_border_on.render(mydest.inflate(-4,-4))
        else:
            widget_border_off.render(mydest.inflate(-4,-4))
        myimage = self.font.render( self.text, True, self.color )
        my_state.screen.set_clip( mydest )
        textdest = myimage.get_rect(center=mydest.center)
        my_state.screen.blit( myimage , textdest )
        my_state.screen.set_clip( None )
        if my_state.active_widget is self:
            self.input_cursor.render( textdest.topright , ( my_state.anim_phase // 3 ) % 4 )

    def _builtin_responder(self,ev):
        if my_state.active_widget is self:
            if ev.type == pygame.KEYDOWN:
                if (ev.key == pygame.K_BACKSPACE) and (len(self.char_list) > 0):
                    del self.char_list[-1]
                elif (ev.unicode in self.ALLOWABLE_CHARACTERS) and (len(ev.unicode) > 0):
                    self.char_list.append(ev.unicode)

    def is_kb_selectable(self):
        return True

    def flash_when_active(self):
        pass

    @property
    def text(self):
        return "".join(self.char_list)


class RadioButtonWidget( Widget ):
    def __init__( self, dx, dy, w, h, sprite=None, buttons=(), spacing=2, **kwargs ):
        # buttons is a list of tuples of (on_frame,off_frame,on_click,tooltip)
        super(RadioButtonWidget, self).__init__(dx,dy,w,h,**kwargs)
        self.sprite = sprite
        self.buttons = list()
        self.spacing = spacing
        ddx = 0
        for b in buttons:
            self.buttons.append(ButtonWidget(ddx,0,sprite.frame_width,sprite.frame_height,sprite,frame=b[1],on_frame=b[0],off_frame=b[1],on_click=self.click_radio,data=b[2],tooltip=b[3],parent=self,anchor=frects.ANCHOR_UPPERLEFT))
            ddx += sprite.frame_width + self.spacing
        self.buttons[0].frame = self.buttons[0].on_frame
        self.active_button = self.buttons[0]
        self.children += self.buttons

    def activate_button( self, button ):
        self.active_button.frame = self.active_button.off_frame
        self.active_button = button
        button.frame = button.on_frame

    def click_radio( self, button, ev ):
        self.activate_button( button )
        if button.data:
            button.data(button,ev)

class ColumnWidget(Widget):
    def __init__( self, dx, dy, w, h, draw_border=False, border=default_border, padding=5, **kwargs ):
        super(ColumnWidget, self).__init__(dx,dy,w,h,**kwargs)
        self.draw_border = draw_border
        self.border = border
        self._interior_widgets = list()
        self._header_widget = None
        self.padding = padding
    def add_interior(self,other_w):
        self.children.append(other_w)
        self._interior_widgets.append(other_w)
        # Set the position of other_w inside this widget.
        other_w.parent = self
        self._position_contents()

    def set_header(self,other_w):
        self.children.append(other_w)
        self._header_widget = other_w
        # Set the position of other_w inside this widget.
        other_w.parent = self
        self._position_contents()

    def clear(self):
        del self._interior_widgets[:]
        del self.children[:]
        self._header_widget = None

    def _position_contents(self):
        dy = 0
        if self._header_widget:
            self._header_widget.dx = -(self._header_widget.w // 2)
            self._header_widget.dy = -(self._header_widget.h // 2)
            self._header_widget.anchor = frects.ANCHOR_TOP
            dy += self._header_widget.h // 2 + self.padding
        for widg in self._interior_widgets:
            widg.dx = 0
            widg.dy = dy
            widg.anchor = frects.ANCHOR_UPPERLEFT
            dy += widg.h + self.padding
        self.h = dy

    def render(self):
        if self.draw_border:
            self.border.render(self.get_rect())

class ScrollColumnWidget(Widget):
    def __init__( self, dx, dy, w, h, up_button, down_button, draw_border=False, border=default_border, padding=5, **kwargs ):
        super(ScrollColumnWidget, self).__init__(dx,dy,w,h,**kwargs)
        self.draw_border = draw_border
        self.border = border
        self._interior_widgets = list()
        self.padding = padding
        self.top_widget = 0
        self.up_button = up_button
        self.up_button.on_click = self.scroll_up
        self.up_button.frame = self.up_button.off_frame
        self.down_button = down_button
        self.down_button.on_click = self.scroll_down
        self.down_button.frame = self.down_button.off_frame

    def add_interior(self,other_w):
        self.children.append(other_w)
        self._interior_widgets.append(other_w)
        # Set the position of other_w inside this widget.
        other_w.parent = self
        other_w.dx = 0
        other_w.anchor = frects.ANCHOR_UPPERLEFT
        self._position_contents()

    def clear(self):
        for w in list(self._interior_widgets):
            self._interior_widgets.remove(w)
            self.children.remove(w)

    def _position_contents(self):
        # Disable all interior widgets, except those currently visible.
        for w in self._interior_widgets:
            w.active = False
        dy = 0
        n = self.top_widget
        if n >= len(self._interior_widgets):
            n = 0
        while (dy < self.h) and (n < len(self._interior_widgets)):
            widg = self._interior_widgets[n]
            widg.dy = dy
            if (dy==0) or (dy + widg.h + self.padding <= self.h):
                widg.active = True
            dy += widg.h + self.padding
            n += 1
        # Activate or deactivate the up/down buttons.
        if self.top_widget > 0:
            self.up_button.frame = self.up_button.on_frame
        else:
            self.up_button.frame = self.up_button.off_frame
        if self._interior_widgets and not self._interior_widgets[-1].active:
            self.down_button.frame = self.down_button.on_frame
        else:
            self.down_button.frame = self.down_button.off_frame

    def scroll_up(self,*args):
        if self.top_widget > 0:
            self.top_widget -= 1
            self._position_contents()

    def scroll_down(self,*args):
        if self._interior_widgets and not self._interior_widgets[-1].active:
            self.top_widget += 1
            self._position_contents()

    def sort(self,key=None):
        self._interior_widgets.sort(key=key)
        self._position_contents()

    def _builtin_responder(self,ev):
        if (ev.type == pygame.MOUSEBUTTONDOWN) and self.get_rect().collidepoint(pygame.mouse.get_pos()):
            if (ev.button == 4):
                self.scroll_up()
            elif (ev.button == 5):
                self.scroll_down()

    def render(self):
        if self.draw_border:
            self.border.render(self.get_rect())

class RowWidget(Widget):
    def __init__( self, dx, dy, w, h, draw_border=False, border=default_border, padding=5, **kwargs ):
        super(RowWidget, self).__init__(dx,dy,w,h,**kwargs)
        self.draw_border = draw_border
        self.border = border
        self._left_widgets = list()
        self._center_widgets = list()
        self._right_widgets = list()
        self.padding = padding

    def add_left(self,other_w):
        self.children.append(other_w)
        self._left_widgets.append(other_w)
        # Set the position of other_w inside this widget.
        other_w.parent = self
        self._position_contents()

    def add_center(self,other_w):
        self.children.append(other_w)
        self._center_widgets.append(other_w)
        # Set the position of other_w inside this widget.
        other_w.parent = self
        self._position_contents()

    def add_right(self,other_w):
        self.children.append(other_w)
        self._right_widgets.append(other_w)
        # Set the position of other_w inside this widget.
        other_w.parent = self
        self._position_contents()

    def _position_contents(self):
        dx = 0
        self.h = max(w.h for w in self._right_widgets + self._center_widgets + self._left_widgets)
        for widg in self._left_widgets:
            widg.dx = dx
            widg.dy = -widg.h//2
            widg.anchor = frects.ANCHOR_LEFT
            dx += widg.w + self.padding

        if self._center_widgets:
            dx = -(sum(w.w for w in self._center_widgets) + (len(self._center_widgets) - 1) * self.padding)//2
            for widg in self._center_widgets:
                widg.dx = dx
                widg.dy = -widg.h//2
                widg.anchor = frects.ANCHOR_CENTER
                dx += widg.w + self.padding

        if self._right_widgets:
            dx = -sum(w.w for w in self._right_widgets) - (len(self._right_widgets) - 1) * self.padding
            for widg in self._right_widgets:
                widg.dx = dx
                widg.dy = -widg.h//2
                widg.anchor = frects.ANCHOR_RIGHT
                dx += widg.w + self.padding

    def render(self):
        if self.draw_border:
            self.border.render(self.get_rect())

class DropdownWidget( Widget ):
    def __init__( self, dx, dy, w, h, color=None, font=None, justify=-1, on_select=None, **kwargs ):
        # on_select is a callable that takes the menu query result as its argument
        super(DropdownWidget, self).__init__(dx,dy,w,h,**kwargs)
        self.color = color or TEXT_COLOR
        self.font = font or my_state.small_font
        self.on_select = on_select
        self.on_click = self.open_menu
        self.menu = rpgmenu.Menu(dx,dy,w,150,border=popup_menu_border,font=font,anchor=frects.ANCHOR_UPPERLEFT)
    def render( self ):
        mydest = self.get_rect()
        if self is my_state.active_widget:
            widget_border_on.render(mydest.inflate(-4,-4))
        else:
            widget_border_off.render(mydest.inflate(-4,-4))
        myimage = self.font.render( str(self.menu.get_current_item()), True, self.color )
        my_state.screen.set_clip( mydest )
        textdest = myimage.get_rect(center=mydest.center)
        my_state.screen.blit( myimage , textdest )
        my_state.screen.set_clip( None )
    def add_item(self,msg,value,desc=None):
        self.menu.add_item(msg,value,desc)
    def open_menu(self,also_self_probably,ev):
        mydest = self.get_rect()
        mydest.h = self.menu.h
        mydest.clamp_ip(my_state.screen.get_rect())
        self.menu.dx,self.menu.dy = mydest.x,mydest.y
        result = self.menu.query()
        if self.on_select:
            self.on_select(result)
    @property
    def value(self):
        return self.menu.get_current_value()

