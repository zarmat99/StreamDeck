import customtkinter
import tkinter as tk
import math


class PotentiometerWidget(customtkinter.CTkCanvas):
    def __init__(self, master, radius, color="gray20", pot_func="linear", range_max=1000, **kwargs):
        super().__init__(master, **kwargs)
        self.circle = None
        self.configure(bg=color, highlightbackground=color)
        self.angle_degrees_limit = 270
        self.pot_value = 0
        self.pot_func = pot_func
        self.radius = radius
        self.center_x = 0
        self.center_y = 0
        self.current_ray = None
        self.starting_angle_degrees = -45
        self.range_max = range_max
        self.range_min = 1 # always equals 1
        self.log_speed_factor = 2
        self.bind("<Configure>", self.setup)
        # self.bind("<Button-1>", self.draw_ray_by_click)
        # self.bind("<B1-Motion>", self.draw_ray_by_click)

    def setup(self, event):
        self.config(width=self.radius * 2, height=self.radius * 2)
        self.delete("all")
        w = event.width
        h = event.height
        self.center_x = w / 2
        self.center_y = h / 2
        x = self.center_x
        y = self.center_y
        self.circle = self.create_oval(x - self.radius, y - self.radius, x + self.radius, y + self.radius,
                                       outline="black", fill="grey", width=4, tags="circle")
        self.after(10, self.draw_initial_ray)

    def draw_initial_ray(self):
        self.draw_ray_by_value(self.pot_value)

    def draw_ray_by_value(self, value):
        self.delete("ray")
        angle_degrees = self.calculate_angle_by_value(value)
        self.current_ray = self.create_line(self.center_x, self.center_y, * self.calculate_endpoint(angle_degrees),
                                            width=8, fill="black", tags="ray")

    def calculate_angle_by_value(self, value):
        if self.pot_func == "linear":
            angle_degrees = self.starting_angle_degrees + (1 - value / self.range_max) * self.angle_degrees_limit
        elif self.pot_func == "logarithmic":
            angle_degrees = self.starting_angle_degrees + (1 - math.log(value + 1, self.log_speed_factor) / math.log(self.range_max + 1, self.log_speed_factor)) * self.angle_degrees_limit
        else:
            raise ValueError("Invalid pot_func")

        return angle_degrees

    def calculate_endpoint(self, angle_degrees):
        angle_radians = math.radians(angle_degrees)
        x_endpoint = self.center_x + self.radius * math.cos(angle_radians)
        y_endpoint = self.center_y - self.radius * math.sin(angle_radians)

        return x_endpoint, y_endpoint


class PotentiometerApp:
    def __init__(self, root):
        self.root = root
        self.potentiometer = PotentiometerWidget(root, color="gray20", radius=100)
        self.potentiometer.pack(expand=True, fill=tk.BOTH)

        self.scale = tk.Scale(root, from_=0, to=1000, orient=tk.HORIZONTAL, command=self.update_potentiometer)
        self.scale.pack(pady=20)

    def update_potentiometer(self, value):
        self.potentiometer.pot_value = float(value)
        self.potentiometer.draw_ray_by_value(int(value))


if __name__ == "__main__":
    root = tk.Tk()
    app = PotentiometerApp(root)
    root.mainloop()


    '''
    def draw_ray_by_click(self, event):
        if self.current_ray:
            self.delete(self.current_ray)

        x, y = event.x, event.y
        print(f"click (x, y): ({x}, {y})")
        angle = math.atan2(self.center_y - y, x - self.center_x)
        angle_degrees = angle * (180.0 / math.pi)

        if -135 <= angle_degrees <= -90:
            self.angle_degrees_limit = -135
        elif -90 <= angle_degrees <= -45:
            self.angle_degrees_limit = -45
        else:
            self.angle_degrees_limit = angle_degrees

        angle_radians = self.angle_degrees_limit * (math.pi / 180.0)
        x1 = self.center_x + self.radius * math.cos(angle_radians)
        y1 = self.center_y - self.radius * math.sin(angle_radians)

        self.current_ray = self.create_line(self.center_x, self.center_y, x1, y1, fill="black", width=8)
        # self.map_pot_value(self.angle_degrees_limit)

    def draw_initial_ray(self):
        initial_angle_degrees = self.starting_angle_degrees
        initial_angle_radians = initial_angle_degrees * (math.pi / 180.0)
        x1 = self.center_x + self.radius * math.cos(initial_angle_radians)
        y1 = self.center_y - self.radius * math.sin(initial_angle_radians)

        self.current_ray = self.create_line(self.center_x, self.center_y, x1, y1, fill="black", width=8)

    def map_pot_value(self, angle_degrees_limit):
        if -180 <= angle_degrees_limit <= -135:
            angle_map = abs(angle_degrees_limit + 135)
        elif -45 <= angle_degrees_limit <= 180:
            angle_map = 225 - angle_degrees_limit
        else:
            angle_map = "None"

        pot_value_range_max = int((int(angle_map) / 270) * (self.range_max - 1)) + 1
        if self.pot_func == "exp":
            # y = a + e^(b * x)
            # find a, b -> conditions: pass through P1(0, 1) and P2(max, max) because we want to map range the linear
            #                          range [0, max] in exponential range [1, max]
            #
            # pass through P1(0, 1)       -> 1 = a + e^(b * 0)
            #                                a = 0
            # pass through P2(max, max) -> max = e^(b * max)
            #                                b = ln(max) / max
            # y = e^(ln(max) / max * x) is equal to max^(x/max), so:
            pot_value_range_max_log = self.range_max ** (pot_value_range_max / self.range_max)
            self.pot_value = pot_value_range_max_log
        elif self.pot_func == "linear":
            self.pot_value = pot_value_range_max

        print(f"degrees angle limited: {angle_degrees_limit}")
        print(f"angle map = {angle_map}")
        print(f"pot_value_range_max = {pot_value_range_max}")
        if self.pot_func == "exp":
            print(f"pot_value_range_max_log = {int(pot_value_range_max_log)}\n")
            
    def serial_send(self, value):
        self.ser.write(str(value).encode())
        
    def linear_value(self, x1, y1, x2, y2, x):
        m = (y2 - y1) / (x2 - x1)
        q = y1 - m * x1
        return m * x + q
    '''
