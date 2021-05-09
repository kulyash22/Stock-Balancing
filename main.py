from flask import Flask, render_template, request, redirect, url_for, make_response
import pandas as pd
import cplex
import docplex
import csv
from io import StringIO

"""
ISSUES
-complete excel sheet 
-grid wise
-credits and teamname
-partial coloring
-description path wise and product wise
-change dec places
-maverick size dikkat
-compute function add
-select me dikh raha/ error handling (optional)
"""

app = Flask(__name__)

def compute():
    #do cplex computation
    pass

def givedfnum():
    df = pd.read_excel('Data.xlsx')
    df.head()

    # sorting the data according to 'SKU' firstly and 'Supply Site Code' secondly to group all the edges of the same grid together -->
    df = df.sort_values(["SKU", "Supply Site Code"], ascending = (True, True))
    df.head()

    # removing unwanted columns from the data -->
    remove_columns = ['Current CS/MIN', 'Current CS/ROP', 'Current CS/MAX']
    df.drop(labels = remove_columns, axis=1, inplace=True)
    df.head()

    # renaming the column titles for our convenience and creating a new dataframe 'df_new' -->
    df_new = df.rename(columns={"Supply Site Code": "B", "Location Code": "D", "Location Type": "Type", "MinDOC (Hl)": "MIN", "Reorder Point (Hl)": "ROP", "MaxDOC (Hl)": "MAX", "Distributor Orders": "Orders", "Available to Deploy": "M", "Closing Stock": "CS"}, inplace = False)
    df_new.head()

    # removing the rows where 'ROP' is zero -->
    df_new = df_new[df_new.ROP != 0]

    # removing the rows where 'Available to Deploy' = 'M' is zero (also 'Scenario' is zero in such cases) -->
    df_new = df_new[df_new.M != 0]
    df_new.head(30)

    # converting the dataframe to a numpy array (2D) for our convenience -->
    df_num = df_new.to_numpy()
    return df_num

def options(strin):
    df_num = givedfnum()
    leftdict = {}
    optionsleft = []
    for i in range(len(df_num)):
        leftdict[df_num[i][0]] = 0
    for i in range(len(df_num)):
        if leftdict[df_num[i][0]] == 0:
            optionsleft.append(df_num[i][0])
        leftdict[df_num[i][0]] = 1 

    optionsright = []
    myset = set()
    if strin!="none":
        for i in range(len(df_num)):
            if(df_num[i][0]==strin):
                myset.add(df_num[i][2])
    
    for x in myset:
        optionsright.append(x)

    optionsleft.sort()
    optionsright.sort()
    return optionsleft, optionsright

def dicti():
    f = open("output.txt", "r")
    strin = str(f.read())
    df_num = givedfnum()
    dct = {}
    for i in range(len(strin)):
        if strin[i]=='X':
            temp = i+30
            answer = ""
            while strin[temp]!='\n':
                answer = answer + strin[temp]
                temp = temp+1
            dct.setdefault((strin[i+2:i+9],strin[i+13:i+20]),[]).append((strin[i+24:i+29],round(float(answer),3)))

    for i in range(len(df_num)):
        key = (df_num[i][0],df_num[i][2]) 
        if key not in dct:
            dct.setdefault((df_num[i][0],df_num[i][2]) ,[]).append((str(df_num[i][1]),0))
        else:
            temp_arr = dct[key]
            ok = False
            for j in range(len(temp_arr)):
                if temp_arr[j][0] == str(df_num[i][1]):
                    ok = True
                    break
            if not ok:
                dct.setdefault((df_num[i][0],df_num[i][2]) ,[]).append((str(df_num[i][1]),0))
    return dct

def getproducts():
    df_num = givedfnum()
    prod = set()
    for i in range(len(df_num)):
        prod.add(df_num[i][1])
    prods = []
    for i in prod:
        prods.append(i)
    prods.sort()
    return prods

def getpaths(val):
    dict = dicti()
    ret = []
    amounts = []
    # print(dict)
    for key, value in dict.items():
        # print(value + " " + val)
        for i in value:
            if str(i[0])==str(val) and i[1]!=0:
                ret.append(key)
                amounts.append(i[1])
                break
    final = []
    for i in range(len(ret)):
        final.append((ret[i][0],ret[i][1],amounts[i]))
    return final

def getgrid():
    grid_dict = {}
    df_num = givedfnum()
    dct = dicti()
    # depot, to_be_transported, initial CS/ROP, final CS/ROP, scenario
    for i in range(len(df_num)):
        brew = df_num[i][0]
        sku = df_num[i][1]
        dep = df_num[i][2]
        cs = df_num[i][7]
        rop = df_num[i][5]
        sc = df_num[i][10]
        val = 0
        temp_arr = dct[(brew,dep)]
        for j in range(len(temp_arr)):
            if temp_arr[j][0] == sku:
                val = temp_arr[j][1]
                break
        grid_dict.setdefault((sku,brew) ,[]).append((dep, val, cs/rop, (cs + val)/rop, sc))
    return grid_dict

                
@app.route('/',methods=['POST','GET'])
def home():
    return render_template('homepage.html')

@app.route('/home',methods=['POST','GET'])
def main():
    if request.method == 'POST':
        val = request.form['answer']
        return redirect(url_for('.second_page',arg=val))      
    left, right = options("none")
    return render_template('index.html',opns=left)

@app.route('/productwise',methods=['POST','GET'])
def productwise():
    if request.method=='POST':
        val = request.form['answer']
        return redirect(url_for('.prodresult',arg=val))
    products = getproducts()
    return render_template('productlist.html',opns=products)

@app.route('/prodresult',methods=['POST','GET'])
def prodresult():
    if request.method == 'POST':
        val = request.form['val']
        si = StringIO()
        cw = csv.writer(si)
        cw.writerows(getpaths(val))
        output = make_response(si.getvalue())
        filename = str(val)+" deliveries.csv"
        output.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
        output.headers["Content-type"] = "text/csv"
        return output
    val = request.args['arg']
    prods = getpaths(val)
    return render_template('prodresult.html',result = prods,val1=val)

@app.route('/another',methods=['POST','GET'])
def second_page():
    if request.method == 'POST':
        val1 = request.form['answer1']
        val2 = request.form['answer2']
        return redirect(url_for('.result',fromm=val1,too=val2))     
    val = request.args['arg']
    left, right = options(str(val))
    return render_template('secondarg.html',opns=right,arg=val)

@app.route('/result',methods=['POST','GET'])
def result():
    if request.method == 'POST':
        joinval = request.form['val']
        joinval = joinval.split()
        val1,val2 = joinval[0],joinval[1]
        si = StringIO()
        cw = csv.writer(si)
        lis = dicti()[val1,val2]
        for row in lis:
            if row[1]!=0:
                cw.writerow(row)
        output = make_response(si.getvalue())
        filename = str(val1) + " to " + str(val2) +" deliveries.csv"
        output.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
        output.headers["Content-type"] = "text/csv"
        return output
    val1 = request.args['fromm']
    val2 = request.args['too']
    dict = dicti()
    result = dict[(val1,val2)]
    joinval = str(val1)+" "+str(val2)
    return render_template('result.html',result=result,val1=val1,val2=val2,joinval=joinval)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000, debug = True)
