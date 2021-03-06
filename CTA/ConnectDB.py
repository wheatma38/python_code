# -=-=-=-=-=-=-=-=-=-=-=
# coding=UTF-8
# __author__='Guo Jun'
# Version 1.0.0
# -=-=-=-=-=-=-=-=-=-=-=
import pymysql
import pandas as pd


def connDB():  # 连接数据库函数
    conn = pymysql.connect(host='localhost', user='root', passwd='66196619', db='data', charset='utf8')
    cur = conn.cursor();
    return (conn, cur);


def exeUpdate(cur, sql):  # 更新语句，可执行update,insert语句
    sta = cur.execute(sql);
    return (sta);

def fill_data(query_sql):
    conn, cur = connDB()
    try:
        cur.execute(query_sql)
    except Exception as e:
        print(e)
        print(query_sql)
    conn.commit()
    conn.close();

def exeDelete(cur, IDs):  # 删除语句，可批量删除
    for eachID in IDs.split(' '):
        sta = cur.execute('delete from relationTriple where tID =%d' % int(eachID));
    return (sta);


def exeQuery(cur, sql):  # 查询语句
    cur.execute(sql);
    return (cur);


def connClose(conn, cur):  # 关闭所有连接
    cur.close();
    conn.commit();
    conn.close();


def get_data(items, table, symbol, startDate, endDate):
    conn, cur = connDB()
    query_sql = 'select ' + items + ' from data.' + table + ' where symbol in ('+ str(symbol).replace('[','').replace(']','') + ') and date between \'' + startDate + '\' and \'' + endDate + '\' order by symbol, date'
    # print(query_sql)
    try:
        cur.execute(query_sql)
        db_data = cur.fetchall()
    except Exception as e:
        print(e)
        print(query_sql)
    conn.commit()
    connClose(conn, cur)
    return (db_data)


def get_all_data(items, table, condition):
    conn, cur = connDB()
    query_sql = 'select ' + items + ' from ' + table + ' ' + condition

    try:
        cur.execute(query_sql)
        db_data = cur.fetchall()
    except Exception as e:
        print(e)
        db_data =[]

    connClose(conn, cur)
    return (db_data)

def get_ft(symbol, start_time, end_time):
    items = 'datetime, open, high, low, close'
    table = ' fur_price_5m'
    condition = 'where symbol = \'' + symbol + '\' and datetime >= \'' + start_time + '\' and datetime <= \'' + end_time + '\'  order by datetime asc'
    symbol_data = get_all_data(items, table, condition)
    k_data = pd.DataFrame(list(symbol_data), columns=['datetime', 'open', 'high', 'low', 'close'])
    k_data.set_index(["datetime"], inplace=True)
    k_data = k_data.astype('float64').round(2)
    k_data = k_data.reset_index(["datetime"])
    return k_data