import customtkinter as ctk
from depth_camera.config import *
from depth_camera.tools import DepthCamera
from depth_camera.utils import _convert_to_pil

class Frame(ctk.CTkFrame):
    def __init__(self, container, text, side='left'):
        ctk.CTkFrame.__init__(self, container)
        self.setup(text=text, side=side)
        
        self.config_size = {
            'image_size': [640, 480],
            'current_size': [640, 480],
            'min_size': [100, 100],
        }
    
    def setup(self, text, side):
        self.out = ctk.CTkLabel(self, text=text, font= ("sans-serif", 15))
        self.out.pack(fill='both', expand=True, padx=5, pady=5)
        self.out.configure(anchor='center')
        self.img_label = ctk.CTkLabel(self, text="")
        self.img_label.pack(side=side, fill="both", expand=True, padx=5, pady=5)
    
    def img_update(self, img):
        self.img_label.configure(image=img)
        self.img = img

# class Button(ctk.CTkButton):
#     def __init__(self, container, **kwargs):
#         ctk.CTkButton.__init__(self, container, **kwargs)
#         self._config()
        
#     def _config(self, text):
#         self.out = ctk.CTkLabel(self, text=text, font= ("sans-serif", 15))

class CheckBox(ctk.CTkCheckBox):
    def __init__(self, container, **kwargs):
        ctk.CTkCheckBox.__init__(self, container, **kwargs)
        self._config()
    
    def _config(self):
        pass

class Slider(ctk.CTkSlider):
    def __init__(self, container, **kwargs):
        ctk.CTkSlider.__init__(self, container, **kwargs)
        self._config()
    
    def _config(self):
        pass
        

class App():
    def __init__(self, 
                 camera,
                 robot=None,
                 title='Orbecc Camera GUI', 
                 size=None, 
                 icon=ICON_PATH):
        self.isrun = False
        
        self.window = ctk.CTk()
        self.window.iconbitmap(icon)
        self.window.title(title)
        
        self.camera = camera
        
        self.config_size = {
            'init_size': [1360, 1080],
            'current_size': [1360, 1080],
            'min_size': [920, 720],
            'im_size':[self.camera.width, self.camera.height]
        }
        
        self.window.minsize(self.config_size['min_size'][0], self.config_size['min_size'][1])        
        if size:
            self.window.geometry(f"{size}")
        else :
            self.window.geometry(f"{self.config_size['init_size'][0]}x{self.config_size['init_size'][1]}")
        
        if self.camera.save_data:
            self.camera.data.setup()
        
        if self.camera.thread_progress:
            self.camera.thread.start()
        
        if robot is not None:
            self.camera.robot = robot
        
        self.__setup()
        
    def __setup(self):

        self.__add_color_frame()
            
        if self.camera.depth : 
            self.__add_depth_frame()
        
        self.__add_temporal_filter_cb()
        self.__add_yolo_cb()
        self.__add_colormap_cb()
        self.__add_gripper_slider()
        
    def __add_color_frame(self):
        self.color_frame_display = Frame(self.window, 'Color Frame')
        self.color_frame_display.place(relx=0, rely=0.4, x=0, anchor='w')
        
    def __add_depth_frame(self):
        self.depth_frame_display = Frame(self.window, 'Depth Frame')
        self.depth_frame_display.place(relx=1, rely=0.4, x=-10, anchor='e')
    
    def __add_temporal_filter_cb(self):
        temporal_filter_cb = CheckBox(self.window, 
                                    #   variable=self.camera.temporal_filter
                                      onvalue='on', offvalue='off', text='Temporal Filter'
                                      )
        temporal_filter_cb.place(x=10, y=7)
    
    def __add_yolo_cb(self):
        self.yolo_var = ctk.StringVar(value='on')
        yolo_cb = CheckBox(self.window, 
                        #    variable=self.yolo_var, command=self.__cb_command('yolo'),
                           onvalue='on', offvalue='off', text='YOLOv8')
        yolo_cb.place(x=180, y=7)
    
    def __add_colormap_cb(self):
        self.yolo_var = ctk.StringVar(value='on')
        yolo_cb = CheckBox(self.window, 
                        #    variable=self.yolo_var, command=self.__cb_command('yolo'),
                            onvalue='on', offvalue='off', text='ColorMap')
        yolo_cb.place(x=350, y=7)
    
    def __add_gripper_slider(self):
        self.gripper_slider_horizontal = Slider(self.window, from_=0, to=640)
        self.gripper_slider_horizontal.place(x=10, y=600)
        horizontal_label = ctk.CTkLabel(self.window, text='Gripper Horizontal', font=("Arial", 16) )
        horizontal_label.place(x=35, y=565)
        
        self.gripper_slider_vertical = Slider(self.window, from_=0, to=480)
        self.gripper_slider_vertical.place(x=230, y=600)
        vertical_label = ctk.CTkLabel(self.window, text='Gripper Vertical', font=("Arial", 16) )
        vertical_label.place(x=270, y=565)
        
        self.gripper_slider_size = Slider(self.window, from_=0, to=100)
        self.gripper_slider_size.place(x=450, y=600)
        vertical_label = ctk.CTkLabel(self.window, text='Gripper Size', font=("Arial", 16) )
        vertical_label.place(x=500, y=565)
    
    # def __cb_command(self, arg):
    #     if arg == 'temporal':
    #         pass
    #     if arg == 'yolo':
    #         # if self.yolo_var == 'on':
    #         #     self.camera.yolo = True
    #         # else : self.camera.yolo = False
            
    #         pass
            
    def run(self, verbose=False):
        self.isrun = True
        
        self.loop(verbose=verbose)
        self.window.mainloop()

        if self.camera.save_data:
            self.camera.data.save()
        
        self.close()
    
    def loop(self, verbose=False):
        
        gripper_loc = self.gripper_slider_horizontal.get(), self.gripper_slider_vertical.get(), self.gripper_slider_size.get()
        depth_img, _, color_img = self.camera.get_frame(show=False, verbose=verbose, gripper_loc=gripper_loc)
        
        color_img =  _convert_to_pil(color_img, self.config_size['im_size'][0], 
                                     self.config_size['im_size'][1])
        self.color_frame_display.img_update(color_img)
    
        if self.camera.depth:
            depth_img =  _convert_to_pil(depth_img, self.config_size['im_size'][0], 
                                         self.config_size['im_size'][1])
            self.depth_frame_display.img_update(depth_img)
        
        if self.isrun:
            self.window.after(14, self.loop)

    def close(self):
        self.isrun = False
        self.camera.close()

if __name__ == '__main__':
    camera = DepthCamera(cam=0, thread_progress=True)
    app = App(camera)
    app.run(verbose=True)