# 复数数学计算
import cmath

import random

import time


class Sandy:

    def __init__(self, block, x, y):
        self.block = block # 0->up,1->low
        self.x = x
        self.y = y


class SandyClock:
    # 板子是上面的还是下面的
    LOW_BLOCK = 0
    UP_BLOCK = 1

    # 这个位置是否有沙砾
    NO_SANDY = 0
    HAS_SANDY = 1

    # 是否在底边上
    IN_BOTTOM = 0
    NOT_IN_BOTTOM = 1
    IN_X_SLOPE = 2
    IN_Y_SLOPE = 3

    def __init__(self, sandy_list=None, size=None):
        if size is None:
            size = [8, 8, 8, 8]
        self.up_block_x = size[0]
        self.up_block_y = size[1]
        self.low_block_x = size[2]
        self.low_block_y = size[3]

        # 沙砾集合
        if sandy_list is None:
            sandy_list = []
            for i in range(self.up_block_x):
                sandy_list.append(Sandy(SandyClock.LOW_BLOCK, 0, i))
        self.sandy_list = sandy_list

        # 生成棋盘
        self.up_block = [ [ SandyClock.NO_SANDY ] * self.up_block_x for _ in range(self.up_block_y) ]
        self.low_block = [ [ SandyClock.NO_SANDY ] * self.low_block_x for _ in range(self.low_block_y)]

        # 把有沙子的地方赋值为1
        for index, sandy in enumerate(sandy_list):
            if sandy.block == SandyClock.LOW_BLOCK:
                self.low_block[sandy.x][sandy.y] = SandyClock.HAS_SANDY
            elif sandy.block == SandyClock.UP_BLOCK:
                self.up_block[sandy.x][sandy.y] = SandyClock.HAS_SANDY
            else:
                print("傻逼")

        # 重力方向
        self.gravity = [1, 1, 0]


    def shift_sandy_bias(self, sandy_para, gravity):
        global sandy
        sandy = sandy_para
        # 生成dx与dy
        dx = 0
        dy = 0
        if "+x" in gravity:
            dx += 1
        elif "-x" in gravity:
            dx -= 1
        else:
            print("傻逼")
        if "+y" in gravity:
            dy += 1
        elif "-y" in gravity:
            dy -= 1
        else:
            print("傻逼")

        # 判断是在上块还是在下块
        block = "low_block"
        if sandy.block == self.UP_BLOCK:
            block = "up_block"
        elif sandy.block == self.LOW_BLOCK:
            block = "low_block"

        # 判断是否在底边，生成flag
        x_slope_flag = SandyClock.NOT_IN_BOTTOM
        if "+x" in gravity:
            if eval("sandy.x") + 1 > 7:
                x_slope_flag = SandyClock.IN_X_SLOPE
        elif "-x" in gravity:
            if eval("sandy.x") - 1 < 0:
                x_slope_flag = SandyClock.IN_X_SLOPE
        else:
            print("大傻逼")

        y_slope_flag = SandyClock.NOT_IN_BOTTOM
        if "+y" in gravity:
            if eval("sandy.y") + 1 > 7:
                y_slope_flag = SandyClock.IN_Y_SLOPE
        elif "-y" in gravity:
            if eval("sandy.y") - 1 < 0:
                y_slope_flag = SandyClock.IN_Y_SLOPE
        else:
            print("大傻逼")

        bottom_flag = SandyClock.NOT_IN_BOTTOM
        if x_slope_flag == SandyClock.IN_X_SLOPE and y_slope_flag == SandyClock.IN_Y_SLOPE:
            bottom_flag = SandyClock.IN_BOTTOM
        elif x_slope_flag == SandyClock.IN_X_SLOPE:
            bottom_flag = SandyClock.IN_X_SLOPE
        elif y_slope_flag == SandyClock.IN_Y_SLOPE:
            bottom_flag = SandyClock.IN_Y_SLOPE

        # 主判断流程

        # 轻微屎山，up_block与low_block
        if sandy.block == self.UP_BLOCK:
            # 如果在底边，直接返回，不往下走了
            if bottom_flag == SandyClock.IN_BOTTOM:
                print("IN_BOTTOM")
                return
            # 如果在X边，只有y的坐标会发生变化
            elif bottom_flag == SandyClock.IN_X_SLOPE:
                # 说明下面是空的，进行移位
                if self.up_block[sandy.x][sandy.y + dy] == self.NO_SANDY:
                    self.up_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.up_block[sandy.x][sandy.y + dy] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.y += dy
            # 如果在Y边，只有x的坐标会发生变化
            elif bottom_flag == SandyClock.IN_Y_SLOPE:
                # 说明下面是空的，进行移位
                if self.up_block[sandy.x + dx][sandy.y] == self.NO_SANDY:
                    self.up_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.up_block[sandy.x + dx][sandy.y] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.x += dx
            # 如果不在底边上
            elif bottom_flag == SandyClock.NOT_IN_BOTTOM:
                # 说明下面是空的，进行移位
                if self.up_block[sandy.x + dx][sandy.y + dy] == self.NO_SANDY:
                    self.up_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.up_block[sandy.x + dx][sandy.y + dy] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.x += dx
                    sandy.y += dy
                # 下面不是空的就判断斜下面，现在这种写法不是左右随机下落，而是固定方向，先判断Y方向
                # TODO:改为左右随机下落
                elif self.up_block[sandy.x][sandy.y + dy] == self.NO_SANDY:
                    self.up_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.up_block[sandy.x][sandy.y + dy] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.y += dy
                # 再判断X方向
                elif self.up_block[sandy.x + dx][sandy.y] == self.NO_SANDY:
                    self.up_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.up_block[sandy.x + dx][sandy.y] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.x += dx
                else:
                    print("无法下落")

        # 重复上面的，但是是下块，轻微屎山
        elif sandy.block == self.LOW_BLOCK:
            # 如果在底边，直接返回，不往下走了
            if bottom_flag == SandyClock.IN_BOTTOM:
                print("IN_BOTTOM")
                return
            # 如果在X边，只有y的坐标会发生变化
            elif bottom_flag == SandyClock.IN_X_SLOPE:
                # 说明下面是空的，进行移位
                if self.low_block[sandy.x][sandy.y + dy] == self.NO_SANDY:
                    self.low_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.low_block[sandy.x][sandy.y + dy] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.y += dy
            # 如果在Y边，只有x的坐标会发生变化
            elif bottom_flag == SandyClock.IN_Y_SLOPE:
                # 说明下面是空的，进行移位
                if self.low_block[sandy.x + dx][sandy.y] == self.NO_SANDY:
                    self.low_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.low_block[sandy.x + dx][sandy.y] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.x += dx
            # 如果不在底边上
            elif bottom_flag == SandyClock.NOT_IN_BOTTOM:
                # 说明下面是空的，进行移位
                if self.low_block[sandy.x + dx][sandy.y + dy] == self.NO_SANDY:
                    self.low_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.low_block[sandy.x + dx][sandy.y + dy] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.x += dx
                    sandy.y += dy
                # 下面不是空的就判断斜下面，现在这种写法不是左右随机下落，而是固定方向，先判断Y方向
                # TODO:改为左右随机下落
                elif self.low_block[sandy.x][sandy.y + dy] == self.NO_SANDY:
                    self.low_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.low_block[sandy.x][sandy.y + dy] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.y += dy
                # 再判断X方向
                elif self.low_block[sandy.x + dx][sandy.y] == self.NO_SANDY:
                    self.low_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.low_block[sandy.x + dx][sandy.y] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.x += dx
                else:
                    print("无法下落")

    def shift_sandy_straight(self, sandy_para, gravity):
        global sandy
        sandy = sandy_para

        axis = "default"
        if "x" in gravity:
            axis = "x"
        elif "y" in gravity:
            axis = "y"
        else:
            print("傻逼")

        # 生成dx与dy
        dx = 0
        dy = 0
        if gravity == "+x":
            dx += 1
        elif gravity == "-x":
            dx -= 1
        elif gravity == "+y":
            dy += 1
        elif gravity == "-y":
            dy -= 1
        else:
            print("傻逼")

        # 判断是否在底边，生成flag
        bottom_flag = SandyClock.NOT_IN_BOTTOM
        if "+" in gravity:
            if eval("sandy." + axis) + 1 > 7:
                bottom_flag = SandyClock.IN_BOTTOM
        elif "-" in gravity:
            if eval("sandy." + axis) - 1 < 0:
                bottom_flag = SandyClock.IN_BOTTOM
        else:
            print("大傻逼")

        # # 判断是在上块还是在下块
        # block = "low_block"
        # if sandy.block == self.UP_BLOCK:
        #     block = "up_block"
        # elif sandy.block == self.LOW_BLOCK:
        #     block = "low_block"

        # 主判断流程
        # 如果在底边，直接返回，不往下走了
        if bottom_flag == SandyClock.IN_BOTTOM:
            print("IN_BOTTOM")
            return
        # 如果不在底边，移位
        elif bottom_flag == SandyClock.NOT_IN_BOTTOM:
            # micropython不支持eval，只能轻微屎山不予处罚
            if sandy.block == self.UP_BLOCK:
                if self.up_block[sandy.x + dx][sandy.y + dy] == self.NO_SANDY:
                    # 说明下面是空的，进行移位
                    self.up_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.up_block[sandy.x + dx][sandy.y + dy] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.x += dx
                    sandy.y += dy
            elif sandy.block == self.LOW_BLOCK:
                if self.low_block[sandy.x + dx][sandy.y + dy] == self.NO_SANDY:
                    # 说明下面是空的，进行移位
                    self.low_block[sandy.x][sandy.y] = self.NO_SANDY
                    self.low_block[sandy.x + dx][sandy.y + dy] = self.HAS_SANDY
                    # 更新sandy的坐标
                    sandy.x += dx
                    sandy.y += dy
        else:
            print("hello,大傻逼")


    # 运行一轮
    def process(self):
        # 根据沙砾的高度排序，算内积
        # 从下往上排
        # self.sandy_list.sort(key=lambda sandy:( sandy.x * self.gravity[0] + sandy.y * self.gravity[1] ),reverse=True )
        # 从上往下排
        # self.sandy_list.sort(key=lambda sandy:( sandy.x * self.gravity[0] + sandy.y * self.gravity[1] ))
        # 猴排
        random.shuffle(self.sandy_list)

        # 判断重力在哪个方向
        # gravity_angle = cmath.phase(complex(self.gravity[0], self.gravity[1]))
        gravity_angle = input("gravity_angle:")
        gravity_angle = float(gravity_angle) * cmath.pi / 180

        for sandy in self.sandy_list:

            if -cmath.pi*7/8 < gravity_angle <= -cmath.pi*5/8: # -x,-y
                self.shift_sandy_bias(sandy,"-x-y")

            elif -cmath.pi*5/8 < gravity_angle <= -cmath.pi*3/8: # -y
                self.shift_sandy_straight(sandy, "-y")

            elif -cmath.pi*3/8 < gravity_angle <= -cmath.pi/8: # +x,-y
                self.shift_sandy_bias(sandy,"+x-y")

            elif -cmath.pi/8 < gravity_angle <= cmath.pi/8: # +x
                self.shift_sandy_straight(sandy, "+x")

            elif cmath.pi/8 < gravity_angle <= cmath.pi*3/8: # +x,+y
                self.shift_sandy_bias(sandy,"+x+y")

            elif cmath.pi*3/8 < gravity_angle <= cmath.pi*5/8: # +y
                self.shift_sandy_straight(sandy, "+y")

            elif cmath.pi*5/8 < gravity_angle <= cmath.pi*7/8: # -x,+y
                self.shift_sandy_bias(sandy,"-x+y")

            elif gravity_angle <= -cmath.pi*7/8 or gravity_angle > cmath.pi*7/8: # -x
                self.shift_sandy_straight(sandy, "-x")


    # 显示
    def display(self):
        # for i in self.up_block:
        #     for j in i:
        #         if j == SandyClock.NO_SANDY:
        #             print("_", end="")
        #         elif j == SandyClock.HAS_SANDY:
        #             print("0", end="")
        #     print("\n")

        print("\n")

        for i in self.low_block:
            for j in i:
                if j == SandyClock.NO_SANDY:
                    print("_", end="")
                elif j == SandyClock.HAS_SANDY:
                    print("0", end="")
            print("\n")

    def display_on_st7789(self):
        # hardware.lcd.fill(st7789.BLACK)
        pass
        for i,val_i in enumerate(self.up_block):
            for j,val_j in enumerate(val_i):
                if val_j == SandyClock.NO_SANDY:
                    # hardware.lcd.fill_rect(i*10,j*10,8,8,st7789.CYAN)
                    pass
                elif val_j == SandyClock.HAS_SANDY:
                    # hardware.lcd.fill_rect(i*10,j*10,8,8,st7789.WHITE)
                    pass

        for i,val_i in enumerate(self.low_block):
            for j,val_j in enumerate(val_i):
                if val_j == SandyClock.NO_SANDY:
                    # hardware.lcd.fill_rect(100+i*10,100+j*10,8,8,st7789.CYAN)
                    pass
                elif val_j == SandyClock.HAS_SANDY:
                    # hardware.lcd.fill_rect(100+i*10,100+j*10,8,8,st7789.WHITE)
                    pass

if __name__ == '__main__':
    # hardware()
    sc = SandyClock()
    sc.display()
    while True:
        sc.process()
        sc.display()
        # time.sleep(1)
