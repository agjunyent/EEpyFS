import PySimpleGUI as sg

class CircularProgressbar():
    def __init__(self, bar_radius=40, bar_width=35, gap=1,
                 bar_color='grey', progress_color='white'):
        self.bar_radius = bar_radius
        self.bar_width = bar_width
        self.bar_color = bar_color
        self.progress_color = progress_color
        self.gap = gap + (self.bar_width + 1) // 2
        self.angle = 0
        self.graph = sg.Graph(
            (2*(self.bar_radius+self.gap), 2*(self.bar_radius+self.gap)),
            (-self.bar_radius-self.gap, -self.bar_radius-self.gap),
            (self.bar_radius+self.gap, self.bar_radius+self.gap))
        self.p = None

    def initiate(self):
        self.graph.draw_circle((0, 0), self.bar_radius,
                               line_color=self.bar_color, line_width=self.bar_width)
        self.set_percent(0)

    def set_percent(self, percent=0):
        angle = 360 * percent / 100
        self.angle = min(360, max(0, int(angle)))
        self.draw()

    def draw(self):
        if self.p:
            self.graph.delete_figure(self.p)
        r = self.bar_radius
        if self.angle == 360:
            self.p = self.graph.draw_circle((0, 0), self.bar_radius, line_color=self.progress_color,
                                            line_width=self.bar_width+1)
        else:
            self.p = self.graph.draw_arc((-r, r), (r, -r), self.angle, 90,
                                         style='arc', arc_color=self.progress_color,
                                         line_width=self.bar_width+1)
        return False
