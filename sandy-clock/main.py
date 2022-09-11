import uos
import machine
from machine import Pin, Timer, I2C, SPI

import st7789 as st7789
from mma7660 import MMA7660
from sr_74hc595_spi import SR

from fonts import vga2_8x8 as font1
from fonts import vga1_16x32 as font2
from fonts import my_16x16 as font3
import random
import framebuf
import uasyncio as asyncio

# 复数数学计算
import cmath

import time

import random

from time import sleep_us


class hardware():  # 初始化屏幕驱动

    lcd = None
    accel = None

    sr_spi = None
    sr = None
    fbuf = None
    buffer = None
    buffer0 = None
    buffer1 = None

    buttonA = None
    buttonB = None

    timer = None

    def __init__(self):
        # 屏幕配置
        st7789_res = 0
        st7789_dc = 1
        spi_sck = machine.Pin(2)
        spi_tx = machine.Pin(3)
        spi = machine.SPI(0, baudrate=4000000, phase=1, polarity=1, sck=spi_sck, mosi=spi_tx)
        lcd = st7789.ST7789(
            spi,
            240,
            240,
            reset=machine.Pin(st7789_res, machine.Pin.OUT),
            dc=machine.Pin(st7789_dc, machine.Pin.OUT),
            rotation=0)
        lcd.fill(st7789.BLACK)
        hardware.lcd = lcd

        # 姿态传感器配置
        i2c = I2C(1, scl=Pin(11), sda=Pin(10))
        accel = MMA7660(i2c)
        accel.on(True)
        hardware.accel = accel

        # led灯板配置
        sr_spi = SPI(1, 5000_000, sck=Pin(26), mosi=Pin(27))
        rclk = Pin(22, Pin.OUT)
        sr = SR(sr_spi, rclk, 2)  # chain of 2 shift registers
        hardware.sr_spi = sr_spi
        hardware.sr = sr

        hardware.buffer1 = bytearray(1)  #
        hardware.buffer0 = bytearray(1)  #
        hardware.buffer = bytearray(8 * 2)  #

        hardware.fbuf = framebuf.FrameBuffer(hardware.buffer, 8 * 2, 8, framebuf.MONO_VLSB)

        # 开放pin脚
        hardware.buttonB = Pin(5, Pin.IN, Pin.PULL_UP)
        hardware.buttonA = Pin(6, Pin.IN, Pin.PULL_UP)


        # 定时器
        hardware.timer = Timer()
        hardware.timer.init(mode=Timer.PERIODIC, period=1000, callback=hardware.update_time)

    # 更新时间
    def update_time(self):
        SandyClock.current_time += 1
        # print("timer run,current time:",SandyClock.current_time)

class Sandy:

    def __init__(self, block, x, y):
        self.block = block  # 0->up,1->low
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


    current_time = 0


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
            for i in range(self.low_block_x):
                sandy_list.append(Sandy(SandyClock.LOW_BLOCK, 0, i))
            for i in range(self.low_block_x):
                sandy_list.append(Sandy(SandyClock.LOW_BLOCK, 2, i))
            for i in range(self.low_block_x):
                sandy_list.append(Sandy(SandyClock.LOW_BLOCK, 4, i))
            for i in range(self.low_block_x):
                sandy_list.append(Sandy(SandyClock.LOW_BLOCK, 6, i))

            # for i in range(self.up_block_x):
            #     sandy_list.append(Sandy(SandyClock.UP_BLOCK, 0, i))
        self.sandy_list = sandy_list

        # 生成棋盘
        self.up_block = [[SandyClock.NO_SANDY] * self.up_block_x for _ in range(self.up_block_y)]
        self.low_block = [[SandyClock.NO_SANDY] * self.low_block_x for _ in range(self.low_block_y)]

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

        # 调速累加值
        self.keyframe_acc = 0
        self.keyframe_target = 1
        self.cross_crack_flag = False



    # 判断是否允许下落
    def update_keyframe(self):
        self.cross_crack_flag = False
        if self.keyframe_acc >= self.keyframe_target:
            self.cross_crack_flag = True
            self.keyframe_acc = 0
        self.keyframe_acc += 1

    def check_button(self):
        btn_val_A = hardware.buttonA.value()
        btn_val_B = hardware.buttonB.value()

        if btn_val_A == 0:
            if self.keyframe_target < 9:
                self.keyframe_target += 1
            else:
                self.keyframe_target = 1
        if btn_val_B == 0:
            SandyClock.current_time = 0
            hardware.lcd.text(font2, 'time:    ', 10, 150, st7789.GREEN, st7789.BLACK)

    # 数值换算
    def position_convert(self, position):
        sign_bit = 1 << 5
        if position & sign_bit == 0:
            sign = 1
        else:
            sign = -1
        if sign > 0:
            value = position & ~sign_bit
        else:
            value = sign * ((sign_bit << 1) - position)
        return value

    # 姿态捕捉
    def update_gravity(self):
        p = bytearray(3)
        hardware.accel.getSample(p)
        y = int(self.position_convert(p[0]) * 2.7)
        x = int(self.position_convert(p[1]) * 2.7)
        z = self.position_convert(p[2])
        return [-x, -y, z]

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
        # 如果在斜底部，判断是否可以移到下一个块中
        if bottom_flag == SandyClock.IN_BOTTOM:
            # print("IN_BOTTOM")

            #只有到了那一帧，才能往下走
            if self.cross_crack_flag == True:
                if sandy.block == SandyClock.LOW_BLOCK:
                    # 下到上，判断是否可以移动
                    if sandy.x == 7 and sandy.y == 7 \
                            and self.up_block[0][0] == SandyClock.NO_SANDY \
                            and gravity == "+x+y":
                        # 移动
                        self.low_block[7][7] = SandyClock.NO_SANDY
                        self.up_block[0][0] = SandyClock.HAS_SANDY
                        # 更新sandy的坐标
                        sandy.block = SandyClock.UP_BLOCK
                        sandy.x = 0
                        sandy.y = 0

                elif sandy.block == SandyClock.UP_BLOCK:
                    # 上到下，判断是否可以移动
                    if sandy.x == 0 and sandy.y == 0 \
                            and self.low_block[7][7] == SandyClock.NO_SANDY \
                            and gravity == "-x-y":
                        # 移动
                        self.up_block[0][0] = SandyClock.NO_SANDY
                        self.low_block[7][7] = SandyClock.HAS_SANDY
                        # 更新sandy的坐标
                        sandy.block = SandyClock.LOW_BLOCK
                        sandy.x = 7
                        sandy.y = 7

                else:
                    print("太傻逼了")

        # 如果不在底边，必定无法到下面的块，再判断
        else:

            # 轻微屎山，up_block与low_block
            if sandy.block == self.UP_BLOCK:
                # 如果在X边，只有y的坐标会发生变化
                if bottom_flag == SandyClock.IN_X_SLOPE:
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
                        # print("无法下落")
                        pass

            # 重复上面的，但是是下块，轻微屎山
            elif sandy.block == self.LOW_BLOCK:
                # 如果在X边，只有y的坐标会发生变化
                if bottom_flag == SandyClock.IN_X_SLOPE:
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
                        pass
                        # print("无法下落")

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
        # 如果在底边，判断是否可以移到下一个块中
        if bottom_flag == SandyClock.IN_BOTTOM:

            # 只有到了累加的关键帧，才能往下漏
            if self.cross_crack_flag == True:

                if sandy.block == SandyClock.LOW_BLOCK:
                    # 下到上，判断是否可以移动
                    if sandy.x == 7 and sandy.y == 7 \
                            and self.up_block[0][0] == SandyClock.NO_SANDY \
                            and (gravity == "+x" or gravity == "+y"):
                        # 移动
                        self.low_block[7][7] = SandyClock.NO_SANDY
                        self.up_block[0][0] = SandyClock.HAS_SANDY
                        # 更新sandy的坐标
                        sandy.block = SandyClock.UP_BLOCK
                        sandy.x = 0
                        sandy.y = 0

                elif sandy.block == SandyClock.UP_BLOCK:
                    # 上到下，判断是否可以移动
                    if sandy.x == 0 and sandy.y == 0 \
                            and self.low_block[7][7] == SandyClock.NO_SANDY \
                            and (gravity == "-x" or gravity == "-y"):
                        # 移动
                        self.up_block[0][0] = SandyClock.NO_SANDY
                        self.low_block[7][7] = SandyClock.HAS_SANDY
                        # 更新sandy的坐标
                        sandy.block = SandyClock.LOW_BLOCK
                        sandy.x = 7
                        sandy.y = 7

                else:
                    print("太傻逼了")

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

        self.check_button()
        self.update_keyframe()

        # 获得重力
        self.gravity = self.update_gravity()
        # print(self.gravity, end="")


        # TODO:加上如果y与之前的y乘积是负数，说明翻过来了，清零


        # 根据沙砾的高度排序，算内积
        # 从下往上排
        # self.sandy_list.sort(key=lambda sandy:( sandy.x * self.gravity[0] + sandy.y * self.gravity[1] ),reverse=True )
        # 从上往下排
        # self.sandy_list.sort(key=lambda sandy:( sandy.x * self.gravity[0] + sandy.y * self.gravity[1] ))
        # 猴排，micropython用不了shuffle，只能自己写
        # random.shuffle(self.sandy_list)
        self.sandy_list.sort(key=lambda sandy: (random.random()))

        # 判断重力在哪个方向
        gravity_angle = cmath.phase(complex(self.gravity[0], self.gravity[1]))
        # print(gravity_angle)

        # 换算
        gravity_angle += cmath.pi / 4

        if -cmath.pi * 7 / 8 < gravity_angle <= -cmath.pi * 5 / 8:  # -x,-y
            for sandy in self.sandy_list:
                self.shift_sandy_bias(sandy, "-x-y")
                # print("-x-y")

        elif -cmath.pi * 5 / 8 < gravity_angle <= -cmath.pi * 3 / 8:  # -y
            for sandy in self.sandy_list:
                self.shift_sandy_straight(sandy, "-y")
                # print("-y")

        elif -cmath.pi * 3 / 8 < gravity_angle <= -cmath.pi / 8:  # +x,-y
            for sandy in self.sandy_list:
                self.shift_sandy_bias(sandy, "+x-y")
                # print("+x-y")

        elif -cmath.pi / 8 < gravity_angle <= cmath.pi / 8:  # +x
            for sandy in self.sandy_list:
                self.shift_sandy_straight(sandy, "+x")
                # print("+x")

        elif cmath.pi / 8 < gravity_angle <= cmath.pi * 3 / 8:  # +x,+y
            for sandy in self.sandy_list:
                self.shift_sandy_bias(sandy, "+x+y")
                # print("+x+y")

        elif cmath.pi * 3 / 8 < gravity_angle <= cmath.pi * 5 / 8:  # +y
            for sandy in self.sandy_list:
                self.shift_sandy_straight(sandy, "+y")
                # print("+y")

        elif cmath.pi * 5 / 8 < gravity_angle <= cmath.pi * 7 / 8:  # -x,+y
            for sandy in self.sandy_list:
                self.shift_sandy_bias(sandy, "-x+y")
                # print("-x+y")

        elif gravity_angle <= -cmath.pi * 7 / 8 or gravity_angle > cmath.pi * 7 / 8:  # -x
            for sandy in self.sandy_list:
                self.shift_sandy_straight(sandy, "-x")
                # print("-x")

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
        hardware.lcd.fill(st7789.BLACK)
        for i, val_i in enumerate(self.low_block):
            for j, val_j in enumerate(val_i):
                if val_j == SandyClock.NO_SANDY:
                    hardware.lcd.fill_rect(j * 10, i * 10, 8, 8, st7789.WHITE)
                elif val_j == SandyClock.HAS_SANDY:
                    hardware.lcd.fill_rect(j * 10, i * 10, 8, 8, st7789.GREEN)

        # for i, val_i in enumerate(self.up_block):
        #     for j, val_j in enumerate(val_i):
        #         if val_j == SandyClock.NO_SANDY:
        #             hardware.lcd.fill_rect(100+j*10,100+i*10,8,8,st7789.WHITE)
        #         elif val_j == SandyClock.HAS_SANDY:
        #             hardware.lcd.fill_rect(100+j*10,100+i*10,8,8,st7789.GREEN)

    def show(self, buf):

        for y in range(8):  # 每循环控制所有灯板同一列
            hardware.buffer1[0] = 0x80  # 选中行
            hardware.buffer1[0] = hardware.buffer1[0] >> y

            for i in range(2):  # 每循环控制一个灯板
                hardware.buffer0[0] = buf[(2 - i) * 8 - 1 - y]  # 选中列
                hardware.sr_spi.write(hardware.buffer0)
                hardware.sr_spi.write(hardware.buffer1)

            hardware.sr.latch()

    def display_on_led_board(self):
        for i, val_i in enumerate(self.low_block):
            for j, val_j in enumerate(val_i):
                if val_j == SandyClock.NO_SANDY:
                    hardware.fbuf.pixel(i + 8, j, 0)
                elif val_j == SandyClock.HAS_SANDY:
                    hardware.fbuf.pixel(i + 8, j, 1)

        for i, val_i in enumerate(self.up_block):
            for j, val_j in enumerate(val_i):
                if val_j == SandyClock.NO_SANDY:
                    hardware.fbuf.pixel(7 - i,7 -  j, 0)
                elif val_j == SandyClock.HAS_SANDY:
                    hardware.fbuf.pixel(7 - i,7 -  j, 1)

        for i in range(100):
            self.show(hardware.buffer)


    def show_time_on_lcd(self):
        hardware.lcd.text(font2, str(self.keyframe_target), 100, 30, st7789.RED, st7789.BLACK)
        hardware.lcd.text(font2, str(self.current_time), 100, 150, st7789.GREEN, st7789.BLACK)


if __name__ == '__main__':
    hardware()

    hardware.lcd.text(font2, "acc:", 10, 30, st7789.RED, st7789.BLACK)
    hardware.lcd.text(font2, "time:", 10, 150, st7789.GREEN, st7789.BLACK)

    sc = SandyClock()

    while True:
        sc.process()
        sc.show_time_on_lcd()

        sc.display_on_led_board()

        # 清屏
        for j in range(2 * 8):
            hardware.buffer[j] = 0x00
        sc.show(hardware.buffer)


        # time.sleep(1)
