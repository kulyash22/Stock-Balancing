# necessary inputs
from flask import Flask, render_template, request, redirect, url_for, make_response
import pandas as pd
import csv
import operator
from io import StringIO

app=Flask(__name__,template_folder='templates')

def givedfnum():
    df = pd.read_excel('Data.xlsx')

    # sorting the data according to 'SKU' firstly and 'Supply Site Code' secondly to group all the edges of the same grid together -->
    df = df.sort_values(["SKU", "Supply Site Code"], ascending = (True, True))

    # removing unwanted columns from the data -->
    remove_columns = ['Current CS/MIN', 'Current CS/ROP', 'Current CS/MAX']
    df.drop(labels = remove_columns, axis=1, inplace=True)

    # renaming the column titles for our convenience and creating a new dataframe 'df_new' -->
    df_new = df.rename(columns={"Supply Site Code": "B", "Location Code": "D", "Location Type": "Type", "MinDOC (Hl)": "MIN", "Reorder Point (Hl)": "ROP", "MaxDOC (Hl)": "MAX", "Distributor Orders": "Orders", "Available to Deploy": "M", "Closing Stock": "CS"}, inplace = False)

    # removing the rows where 'ROP' is zero -->
    df_new = df_new[df_new.ROP != 0]

    # removing the rows where 'Available to Deploy' = 'M' is zero (also 'Scenario' is zero in such cases) -->
    df_new = df_new[df_new.M != 0]

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
        typepl = df_num[i][3]
        if typepl=='DIST':
            type=2
        if typepl == 'DEP':
            type = 1
        if brew==dep:
            type = 0
        val = 0
        temp_arr = dct[(brew,dep)]
        for j in range(len(temp_arr)):
            if str(temp_arr[j][0]) == str(sku):
                val = temp_arr[j][1]
                break
        grid_dict.setdefault((str(sku),str(brew)) ,[]).append((str(dep), str(val), str(round((cs/rop),3)), str(round((cs + val)/rop,3)), str(sc), str(type)))
    for keyy in grid_dict:
        grid_dict[keyy] = sorted(grid_dict[keyy],key = lambda x: x[0])
    return grid_dict

def getbrewsfromprod(sku):
    df_num = givedfnum()
    myset = set()
    for i in range(len(df_num)):
        if str(df_num[i][1])==str(sku):
            myset.add(df_num[i][0])
    print(myset)
    lis = list(myset)
    return lis

def fullpd():
    df = pd.read_excel('Data.xlsx')
    df_num = df.to_numpy()
    dct = dicti()
    output = []
    for i in range(len(df_num)):
        brewery = df_num[i][0]
        depot = df_num[i][2]
        sku = df_num[i][1]
        if (brewery,depot) in dct:
            v = dct[(brewery,depot)]
            ok = False
            for j in v:
                if j[0]==str(sku):
                    ok = True
                    output.append(j[1])
                    break
            if ok==False:
                output.append(0)
        else:
            output.append(0)
    df['Final Output'] = output
    df_final = df.to_numpy()
    return df_final

@app.route('/downmain',methods=['POST','GET'])
def download():
    si = StringIO()
    cw = csv.writer(si)
    lis = fullpd()
    cw.writerow(['Supply Site Code',    'SKU','Location Code',   'Location Type',   'MinDOC (Hl)', 'Reorder Point (Hl)' , 'MaxDOC (Hl)','Closing Stock'   ,'Distributor Orders',  'Current CS/MIN',  'Current CS/ROP'  ,'Current CS/MAX' , 'Available to Deploy', 'Scenario','FINAL AMOUNT (Hl)'])
    for row in lis:
        cw.writerow(row)
    output = make_response(si.getvalue())
    filename = "FINAL_OUTPUT.csv"
    output.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
    output.headers["Content-type"] = "text/csv"
    return output
    return render_template('homepage.html')

                
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

@app.route('/gridwise',methods=['POST','GET'])
def gridwise():
    if request.method=='POST':
        sku = request.form['answer']
        return redirect(url_for('.gridwise2',arg=sku))
    prods = getproducts()
    return render_template('gridlist1.html',opns=prods)

@app.route('/gridwise2',methods=['POST','GET'])
def gridwise2():
    if request.method=='POST':
        val1 = request.form['answer1']
        val2 = request.form['answer2']
        return redirect(url_for('.gridresult',fromm=val1,too=val2))          
    val = request.args['arg']
    brews = getbrewsfromprod(val)
    return render_template('gridlist2.html',opns=brews,arg=val)

@app.route('/gridresult',methods=['POST','GET'])
def gridresult():
    if request.method == 'POST':
        joinval = request.form['val']
        joinval = joinval.split()
        val1,val2 = joinval[0],joinval[1]
        si = StringIO()
        cw = csv.writer(si)
        lis = getgrid()[val1,val2]
        lis = sorted(lis,key = lambda x: x[5])
        for row in lis:
            if row[1]!=0:
                cw.writerow(row)
        output = make_response(si.getvalue())
        filename = "SKU-" + str(val1) + " to " + str(val2) +" deliveries.csv"
        output.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
        output.headers["Content-type"] = "text/csv"
        return output
    val1 = request.args['fromm']
    val2 = request.args['too']
    result = getgrid()[(val1,val2)]
    joinval = str(val1)+" "+str(val2)
    scen = result[0][4]
    result = sorted(result,key = lambda x: x[5])
    return render_template('gridresult.html',result=result,val1=val1,val2=val2,joinval=joinval,scen=scen)

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
    finresult = []
    for i in result:
        if i[1]!=0:
            finresult.append(i)
    joinval = str(val1)+" "+str(val2)
    return render_template('result.html',result=finresult,val1=val1,val2=val2,joinval=joinval)

if __name__ == '__main__':
    app.run(debug = False)
