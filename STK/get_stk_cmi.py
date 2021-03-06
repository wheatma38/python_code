# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
from gm.api import *
from datetime import timedelta, datetime as dt
import talib as ta
import matplotlib.pyplot as plt
from mpl_finance import candlestick_ohlc
import pandas as pd
import numpy as np
from STK.tsdata import get_k_stk as get_k

# 设置token
set_token('73f0f9b75e0ffe88aa3f04caa8d0d9be22ceda2d')

def Run(k_data):
    #实参数据定义##########################
    FEE = 0
    units = 2000

    def MaxDrawDown(return_list):
        max_value = 0
        mdd = 0
        for i in return_list:
            max_value = max(i, max_value)
            if max_value != 0:
                mdd = round(min(mdd, (i - max_value) / max_value),3)
            else:
                mdd = 0
        return(mdd)


    # 获取数据, 创建DataFrame
    k_data['chg'] = (k_data['close'] - k_data['close'].shift(1))/ k_data['close'].shift(1)
    df = k_data.dropna()

    # 定义账户类
    class ActStatus:
        def __init__(self):
            self.datetime = ''
            self.close = 0
            self.chg = 0
            self.pos = 0 # 1 long，-1 short，0 empty
            self.pre_pos = 0

            self.pnl = 0
            self.fee = 0
            self.net_pnl = 0
            self.pnl_rate = 0

        def trade_calc(self, datetime, close, chg, signal, pre_pos):
            self.datetime =datetime
            self.close = close
            self.chg = chg
            self.pos = signal
            self.pre_pos = pre_pos

            self.pnl = self.chg * self.pos * units * self.close
            self.fee = max(abs(self.close * units * abs(self.pos - self.pre_pos)) * FEE, 5 * abs(self.pos - self.pre_pos))
            self.net_pnl = self.pnl - self.fee
            self.pnl_rate = (self.chg - FEE) * self.pos


    # 策略和类初始化数据
    signal = 0
    pre_pos = 0
    rt_list = []
    atr = df.atr.iloc[0]
    pre_close = df.close.iloc[0]
    max_price = 0
    buy_price = 0
    b_day = 0


    for i, row in enumerate(df.iterrows()):
        datetime = row[1].datetime
        close = row[1].close
        chg = row[1].chg
        kod = row[1].kod
        ma = row[1].ma
        b_day  = max(b_day-1, 0)

        if i < 1:  # 从第二条开始
            continue

    ## 数据与信号驱动计算
        rt = ActStatus()
        rt.trade_calc(datetime, close, chg, signal, pre_pos)
        rt_list.append(rt)
        pre_pos = rt.pos


    ## 策略信号
        if kod > ma :
            signal = 1
        elif kod < ma:
            signal = 0
        else:
            signal = pre_pos

        # ATR 止损
        if signal == 1:
            max_price = max(max_price, row[1].high)
        else:
            max_price = 0


        if close < (max_price - 2.2 * atr) and signal == 1:
            signal = 0
        elif b_day != 0:
            signal = 0

        # 百分比止损
        stop_loss = 0.05
        if signal == 1 and close < buy_price * (1 - stop_loss):
            signal = 0
        if pre_pos == 0 and signal == 1:
            buy_price = pre_close
        elif pre_pos == 1 and signal == 0:
            buy_price = 0
            b_day = 3

        ## 保留前一天close数据
        pre_close = close

    # 结果统计与展示
    df_rt = pd.DataFrame()
    df_rt['datetime'] = [rt.datetime for rt in rt_list]
    # df_rt['close'] = [rt.close for rt in rt_list]
    # df_rt['chg'] = [rt.chg for rt in rt_list]
    # df_rt['pos'] = [rt.pos for rt in rt_list]
    # df_rt['pre_pos'] = [rt.pre_pos for rt in rt_list]
    # df_rt['pnl'] = [rt.pnl for rt in rt_list]
    # df_rt['fee'] = [rt.fee for rt in rt_list]
    df_rt.index = [rt.datetime for rt in rt_list]
    df_rt['pnl_rate'] = [rt.pnl_rate for rt in rt_list]
    df_rt['cum_rate'] = round(df_rt['pnl_rate'].cumsum().astype(float) + 1,3)
    max_draw_down = MaxDrawDown(df_rt['cum_rate'])
    df_rt['cum_rate'].plot()
    df_rt = df_rt.set_index('datetime')
    # df = df.set_index('datetime')
    # df_rt = pd.concat([df_rt, df], axis=1)
    # df_rt.to_csv('test.csv')
    # print(df_rt)
    return(df_rt.cum_rate.iloc[-1], max_draw_down,df_rt)


def DrawSignals(k_data):
    # 作图
    stick_freq = 20 # 横坐标间隔

    ## 数据清理，去除非交易时间
    ohlc_data_arr = np.array(k_data[['datetime','open','high','low','close']])
    ohlc_data_arr2 = np.hstack([np.arange(ohlc_data_arr[:, 0].size)[:, np.newaxis], ohlc_data_arr[:, 1:]])
    ndays = ohlc_data_arr2[:, 0]  # array([0, 1, 2, ... n-2, n-1, n])
    date_strings = list(ndays)

    left, width = 0.05, 0.90 ## 定义图横向使用
    rect1 = [left, 0.48, width, 0.50] ## 第一框图高度从0.48~0.98
    rect3 = [left, 0.28, width, 0.20] ## 第二框图高度从0.28~0.48，余下留给了横坐标
    rect2 = [left, 0.08, width, 0.20] ## 第3框图高度从0.08~0.28，余下留给了横坐标

    fig = plt.figure(facecolor='white')
    axescolor = '#f6f6f6'  # the axes background color

    ax = fig.add_axes(rect1, facecolor=axescolor)  # left, bottom, width, height
    ax3 = fig.add_axes(rect3, facecolor=axescolor, sharex=ax)
    ax2 = fig.add_axes(rect2, facecolor=axescolor, sharex=ax)
    # ax2t = ax2.twinx() ## 右侧镜像纵坐标

    # ax3.plot(date_strings, k_data['cmi'], color='red', label='CMI')
    # ax3.plot(date_strings, k_data['cmi_ma'], color='green', label='CMI_MA')
    # # ax3.plot(date_strings, k_data['mfi'] / 100 - 0.5, color='blue', label='MFI')
    # ax3.axhline(20, linestyle='dotted', color='m', lw=1)  ## 画一条水平收益基准线
    # # ax3.axhline(0.15, linestyle='dotted', color='m', lw=1)  ## 画一条水平收益基准线
    # ax3.legend(loc='upper left', frameon=False)
    #
    # ax2.set_xticklabels(date_strings[::stick_freq], rotation=30, ha='right') ## 定义横坐标格式
    # # ax2.plot(date_strings, k_data['bp'] * 100, color='red', label='bp%')
    # ax2.plot(date_strings, k_data['std'], color='blue', label='std')
    # # ax2.plot(date_strings, k_data['cci'], color='blue', label='cci')
    # ax2.legend(loc='upper left', frameon=False)

    # ax2t.set_ylim(float(min(k_data.cci)), float(max(k_data.cci)))
    # ax2t.plot(date_strings, k_data['cci'], color='green', label='cci')
    # ax2t.legend(loc='upper right', frameon=False)
    # ax2t.axhline(100, linestyle='dotted', color='m', lw=1)  ## 画一条水平收益基准线
    # ax2t.axhline(0, linestyle='dotted', color='m', lw=1)  ## 画一条水平收益基准线
    # ax2t.axhline(-100, linestyle='dotted', color='m', lw=1)  ## 画一条水平收益基准线

    # Plot candlestick chart
    candlestick_ohlc(ax, ohlc_data_arr2, width=0.6, colorup='r', colordown='g') ## K线图绘制

    # Format x axis
    ax.set_xticks(ndays[::stick_freq])
    ax.set_xticklabels(date_strings[::stick_freq], rotation=0, ha='right')
    ax.set_xlim(ndays.min(), ndays.max())

    ax.plot(date_strings, k_data['ma'], color='m', label='MA')
    ax.plot(date_strings, k_data['ma_20'], label='MA_20')
    # ax.plot(date_strings, k_data['pn_high'], color='blue', label='pn_high')
    # ax.plot(date_strings, k_data['pn_low'], color='brown', label='pn_low')
    ax.plot(date_strings, k_data['kod'], color='olive', label='KOD')
    # ax.plot(date_strings, k_data['sar'], marker = '*',color='olive', label='SAR', lw=0.5)
    ax.legend(loc='upper left', frameon=False)

    ax.autoscale_view()
    ax.grid(True, linestyle='dotted', linewidth='0.5') ## 背景格线虚化
    ax2.grid(True, linestyle='dotted', linewidth='0.5')
    ax3.grid(True, linestyle='dotted', linewidth='0.5')

    for label in ax.get_xticklabels():
        label.set_visible(False) ## 隐藏第一框图横坐标
    for label in ax3.get_xticklabels():
        label.set_visible(False)  ## 隐藏第一框图横坐标
    plt.show()

def DrawSignals2(k_data):
    # 作图
    stick_freq = 20 # 横坐标间隔

    ## 数据清理，去除非交易时间
    ohlc_data_arr = np.array(k_data[['datetime','open','high','low','close']])
    ohlc_data_arr2 = np.hstack([np.arange(ohlc_data_arr[:, 0].size)[:, np.newaxis], ohlc_data_arr[:, 1:]])
    ndays = ohlc_data_arr2[:, 0]  # array([0, 1, 2, ... n-2, n-1, n])
    date_strings = list(ndays)

    left, width = 0.05, 0.90 ## 定义图横向使用
    rect1 = [left, 0.48, width, 0.50] ## 第一框图高度从0.48~0.98
    rect3 = [left, 0.28, width, 0.20] ## 第二框图高度从0.28~0.48，余下留给了横坐标
    rect2 = [left, 0.08, width, 0.20] ## 第3框图高度从0.08~0.28，余下留给了横坐标

    fig = plt.figure(facecolor='white')
    axescolor = '#f6f6f6'  # the axes background color

    ax = fig.add_axes(rect1, facecolor=axescolor)  # left, bottom, width, height
    ax3 = fig.add_axes(rect3, facecolor=axescolor, sharex=ax)
    ax2 = fig.add_axes(rect2, facecolor=axescolor, sharex=ax)

    ax3.plot(date_strings, k_data['cum_rate'], color='blue', label='c_return')
    ax3.axhline(1, linestyle='dotted', color='m', lw=1)  ## 画一条水平收益基准线
    ax3.legend(loc='upper left', frameon=False)

    ax2.set_xticklabels(date_strings[::stick_freq], rotation=30, ha='right') ## 定义横坐标格式
    ax2.plot(date_strings, k_data['cci30'], color='green', label='cci30')
    ax2.plot(date_strings, k_data['cci60'], color='red', label='cci60')
    ax2.legend(loc='upper left', frameon=False)
    ax2.axhline(100, linestyle='dotted', color='m', lw=1)  ## 画一条水平收益基准线
    ax2.axhline(0, linestyle='dotted', color='m', lw=1)  ## 画一条水平收益基准线
    ax2.axhline(-100, linestyle='dotted', color='m', lw=1)  ## 画一条水平收益基准线

    # Plot candlestick chart
    candlestick_ohlc(ax, ohlc_data_arr2, width=0.6, colorup='r', colordown='g') ## K线图绘制

    # Format x axis
    ax.set_xticks(ndays[::stick_freq])
    ax.set_xticklabels(date_strings[::stick_freq], rotation=0, ha='right')
    ax.set_xlim(ndays.min(), ndays.max())
    ax.legend(loc='upper left', frameon=False)
    ax.autoscale_view()
    ax.grid(True, linestyle='dotted', linewidth='0.5') ## 背景格线虚化
    ax2.grid(True, linestyle='dotted', linewidth='0.5')
    ax3.grid(True, linestyle='dotted', linewidth='0.5')

    for label in ax.get_xticklabels():
        label.set_visible(False) ## 隐藏第一框图横坐标
    for label in ax3.get_xticklabels():
        label.set_visible(False)  ## 隐藏第一框图横坐标
    plt.show()

def ta_cci(n, k_data):
    cci = pd.DataFrame()
    cci['cci'+str(n)] = ta.CCI(k_data.high, k_data.low, k_data.close, timeperiod=n)
    return cci.round(2)

def ta_atr(n, k_data):
    atr = pd.DataFrame()
    atr['atr'] = ta.ATR(k_data.high, k_data.low, k_data.close, timeperiod=n)
    return(atr.round(3))


# cmi_n = 30
# cmi_ma = 5
# cmi_trend = 20
# cmi_choppy = 20
atr_n = 10
n = 20
s_time = '2015-01-01'
e_time = '2018-12-31'
total_return = []
return_m = []
symbol_list = ['SZSE.000002','SZSE.000333','SZSE.002456','SHSE.601318','SHSE.600585','SHSE.600660','SHSE.603288']
# symbol_list = ['SHSE.510880','SZSE.159901','SZSE.159915','SHSE.518880','SZSE.159919','SHSE.510900','SHSE.511260','SHSE.513500','SHSE.510050','SHSE.510500']
# symbol_list = ['SZSE.002456']
# start_list = []
years = int(e_time[:4]) - int(s_time[:4]) + 1
# for n in range(years):
#     if n == 0:
#         start_year = s_time
#         end_year = str(int(s_time[:4]) + n) + '-12-31'
#     elif n == (years - 1):
#         start_year = str(int(s_time[:4]) + n) + '-01-01'
#         end_year = e_time
#     else:
#         start_year = str(int(s_time[:4]) + n) + '-01-01'
#         end_year = str(int(s_time[:4]) + n) + '-12-31'
#     # start_list.append(start_year)
start_year = s_time
end_year = e_time

for i in ['0.618', 'avg4', 'avg3', 'close']:
    for sym in symbol_list:
    # 查询历史行情
    #     df_k = history(symbol=sym, frequency='1h', start_time=start_year, end_time=end_year, fields='eob,open,high,low,close,volume',adjust=1, df=True)
        df_k = get_k(sym, 60, 0, start_year, end_year)
        if len(df_k) == 0:
            continue
        # df_k['cmi'] = abs(df_k.close - df_k.close.shift(cmi_n-1)) * 100 / (df_k.high.rolling(cmi_n).max() - df_k.low.rolling(cmi_n).min())
        # df_k['cmi_ma'] = df_k.cmi.rolling(cmi_ma,min_periods=0).mean()
        if i == '0.618':
            df_k['kod'] = (df_k.high + df_k.low) * 0.191 + (df_k.close * 0.618 + df_k.open * 0.382) * 0.618
        elif i == 'avg4':
            df_k['kod'] = (df_k.high + df_k.low + df_k.close + df_k.open) / 4
        elif i == 'avg3':
            df_k['kod'] = (df_k.high + df_k.low + df_k.close) / 3
        elif i == 'close':
            df_k['kod'] = df_k.close

        df_k['atr'] = ta.ATR(df_k.high, df_k.low, df_k.close, timeperiod=atr_n)
        df_k['ma'] = df_k.close.rolling(20,min_periods=0).mean()

        df_k = df_k.dropna()

        # DrawSignals(df_k)

        re, mdd, df_r = Run(df_k)
        total_return.append([sym, i, re, mdd])

# ret = pd.DataFrame(total_return, columns=['symbol', 'start', 'end', 'return', 'mdd'])
# print(ret)

filename = dt.now().strftime('%Y%m%d_%H%M%S') + '.csv'
t_r=pd.DataFrame(list(total_return))
t_r.to_csv(filename)

