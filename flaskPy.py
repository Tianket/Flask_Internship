from flask import Flask, render_template, request, session
import os
import json
import flask
import pymysql as mysql
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pyecharts import options as opts
from pyecharts.charts import Bar, Line, Pie, Map


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
db = mysql.connect(host='127.0.0.1', user='root', password='123456', db='abc', port=3306, charset='utf8')
cur = db.cursor()


@app.route('/')  # 路由，让前端执行后端路径
def index():
    return render_template("index.html")


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/regin')
def regin():
    return render_template("register.html")


@app.route('/logininfo', methods=['GET', 'POST'])
def logininfo():
    name = request.values.get("usrname")
    pwd = request.values.get("usrpwd")
    session["usr"] = ''
    session["msg"] = ''
    cur.execute("select count(*) num from login where name='{}' and pwd='{}'".format(name, pwd))
    result = cur.fetchall()
    if result[0][0] > 0:
        session["usr"] = name
        return render_template('index.html')
    else:
        session['msg'] = '用户名或密码有误'
        return render_template('login.html')


@app.route('/regininfo', methods=['GET', 'POST'])
def regininfo():
    name = request.values.get("usrname")
    pwd = request.values.get("usrpwd")
    tel = request.values.get("usrtel")
    mail = request.values.get("usrmail")
    gender = request.values.get("usrgen")
    cur.execute("insert into login values(null,'{}','{}','{}','{}','{}')".format(name, pwd, tel, mail, gender))
    db.commit()
    return render_template("login.html")


@app.route("/prov", methods=["GET"])  # 查询省
def prov():
    cur.execute("select * from province")  # id, name
    data = cur.fetchall()  # 列表套元组
    arr = []
    for v in data:
        arr.append({
            "id": v[0],
            "pname": v[1]
        })
        # obj={}
    re = flask.Response(json.dumps({"data": arr}))
    return re


@app.route("/city", methods=["GET"])  # 查询市
def city():
    id = request.values.get("pid")
    cur.execute(
        "select * from city where province_id={}".format(int(id)))  # id,city_index没用 不要了,province_id外键,name, cityname
    data = cur.fetchall()
    arr = []
    for v in data:
        # obj["city_index"]=v[1]
        arr.append({
            "id": v[0],
            "pid": v[2],
            "cname": v[3],
            "cityname": v[4],
        })
    re = flask.Response(json.dumps(arr))
    return re


@app.route('/news')
def news():
    return render_template("new.html")


@app.route('/yubao')  # 跳转天气预报
def yubao():
    return render_template("yubao.html")


@app.route('/aqi')  # 跳转数据分析
def aqi():
    return render_template("aqi.html")


@app.route("/wear", methods=["GET"])  # 查询天气，现爬，把整个标签传过去
def wear():
    city = request.values.get("city")
    req = requests.get("http://www.tianqihoubao.com/yubao/" + city + ".html")
    txt = BeautifulSoup(req.text, "lxml")
    table = txt.find("table")
    table = str(table).replace("/legend", "http://www.tianqihoubao.com/legend")
    re = flask.Response(json.dumps({"data": table}))
    return re


@app.route("/kqzl", methods=["GET"])  # 查询空气质量
def kqzl():
    city = request.values.get("city")
    year = request.values.get("year")

    file_name = "./" + city + "-" + year + ".csv"
    if not os.path.exists(file_name):  # 找不到对应数据文件，直接返回
        json1 = {"msg": "无该城市数据"}
        return flask.Response(json.dumps(json1))

    columns = ["date", "kqzl", "aqi", "pm25", "pm10", "so2", "no2", "co", "o3"]
    df = pd.read_csv(file_name, encoding="gbk", names=columns)  # 读csv
    arr = []

    for idx, row in df.iterrows():  # 迭代函数
        dic = {}
        for col in columns:
            dic[col] = row[col]
        arr.append(dic)

    json1 = {"data": arr, "msg": ""}  # 看数组有没有传过来，搞个空字符串
    re = flask.Response(json.dumps(json1))  # 拼好了传回去
    return re


def df_month(x):
    return x.month


@app.route("/xxt", methods=["GET"])  # 线性图页面
def xxt():
    return render_template("xxt.html")


@app.route("/xxechart", methods=["GET"])  # 线性图表
def xxechart():
    city = request.values.get("city")
    year = request.values.get("year")

    file_name = "./" + city + "-" + year + ".csv"
    if not os.path.exists(file_name):  # 找不到对应数据文件，直接返回
        json1 = {"msg": "无该城市数据"}
        return flask.Response(json.dumps(json1))

    columns = ["date", "kqzl", "aqi", "pm25", "pm10", "so2", "no2", "co", "o3"]
    df = pd.read_csv(file_name, encoding="gbk", names=columns)  # 读csv
    date = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df.index = date

    m = df.groupby(df_month)
    y = m["aqi"].mean().round(2)
    y1 = m['pm10'].mean().round(2)
    y2 = m['pm25'].mean().round(2)
    x = [str(i) + "月" for i in range(1, 13)]

    bar = (
        Bar()
            .add_xaxis(x)
            .add_yaxis("pm10", list(y1), bar_width=25)
            .add_yaxis("pm25", list(y2), bar_width=25)
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
            .set_global_opts(
            title_opts=opts.TitleOpts(title="每月aqi、pm均值数据分析")
        )
    )

    line = Line().add_xaxis(x).add_yaxis("平均aqi", list(y))
    bar.overlap(line)

    return bar.dump_options_with_quotes()


@app.route("/bzt", methods=["GET"])
def bzt():
    return render_template("bzt.html")


@app.route("/bzchart", methods=["GET"])
def bzchart():
    city = request.values.get("city")
    year = request.values.get("year")

    file_name = "./" + city + "-" + year + ".csv"
    if not os.path.exists(file_name):  # 找不到对应数据文件，直接返回
        json1 = {"msg": "无该城市数据"}
        return flask.Response(json.dumps(json1))

    columns = ["date", "kqzl", "aqi", "pm25", "pm10", "so2", "no2", "co", "o3"]
    df = pd.read_csv(file_name, encoding="gbk", names=columns)  # 读csv
    data = df["kqzl"].value_counts()
    x = data.index
    y = data.values
    arr = [int(v) for v in y]
    c = (
        Pie()
            .add("空气质量",
                 [list(z) for z in zip(list(x), arr)],
                 center=["50%", "60%"],
                 radius=["40%", "55%"]
                 )
            .set_global_opts(
            title_opts=opts.TitleOpts(title="全年空气质量总和数据分析", pos_left="center", pos_top="50px"),
            legend_opts=opts.LegendOpts(pos_left="center"),
        )
    )
    return c.dump_options_with_quotes()


@app.route("/geot", methods=["GET"])
def geot():
    return render_template("geot.html")


@app.route("/geochart", methods=["GET"])
def geochart():
    year = request.values.get("year")

    columns = ["date", "kqzl", "aqi", "pm25", "pm10", "so2", "no2", "co", "o3"]
    provinces = ["北京", "成都", "重庆", "上海", "哈尔滨", "天津"]
    province_en = ["beijing", "chengdu", "chongqing", "shanghai", "haerbin", "tianjin"]

    data = []
    for prov in province_en:
        file_name = "./" + prov + "-" + year + ".csv"
        if not os.path.exists(file_name):  # 找不到对应数据文件，直接返回
            data.append(0)
        else:
            df = pd.read_csv(file_name, encoding="gbk", names=columns)  # 读csv
            data.append(int(df['kqzl'].value_counts()['优']))

    c = (
        Map()
            .add("空气质量", [list(z) for z in zip(provinces, data)], "china")
            .set_global_opts(
            title_opts=opts.TitleOpts(title="空气质量均值"),
            visualmap_opts=opts.VisualMapOpts(max_=200),
        )
    )
    print(provinces, data)
    return c.dump_options_with_quotes()


@app.route("/resuser", methods=["GET"])
def resuser():
    user = request.values.get("user")
    cur.execute("select count(*) num from login where user='{}'".format(user))
    data = cur.fetchall()
    josn = {}
    if data[0][0] > 0:
        josn = {"msg": "该用户名已被注册", "flg": False}
    else:
        josn = {"msg": "用户名可以使用", "flg": True}
    re = flask.Response(json.dumps(josn))
    return re


if __name__ == '__main__':
    app.run()
