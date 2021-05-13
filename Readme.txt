---Video_The_Craftsmen has a video on how to run our code

--- We have written the codes in Python and we use Linux, so the attached video has all the commands for Linux (very similar commands for windows exist)

---You need to have some libraries installed to run this local web application. These commands will install the requirements except cplex. 

pip install flask
pip install csv
pip install pandas
pip install numpy
pip install xlrd
pip install openpyxl

---Please install all the above libraries before running our code

---You will have to install cplex's full version from the following link (pip install cplex doesn't work - it only has a promotional version) - Link - 
https://www.ibm.com/in-en/products/ilog-cplex-optimization-studio

---Once CPLEX's full version is installed, link it with Python

---If CPLEX cannot be installed then you can directly use "output.txt" file to view our final solution by simply running the "webapp.py" and NOT "LP_Solver.py" 

---The Data.xlsx contains all the data required to carry out the calculations. 

---Now follow these instructions in order to access the web app.

1) Open the shell, go to the required directory, and run "./LP_Solver.py > output.txt" or its corresponding command in your OS. This will create the output.txt file, which is the solution of the Linear Programming Problem.

2) Run the webapp by executing the command "python3 webapp.py". Use the link generated to access it in your local machine.

Grid wise, path wise and product wise buttons are made so that the final solution can be viewed conveiently.

---------------------

---The main part of our Algorithm -

We are handling each grid independently and each individual grid is obtained by sorting the Data.xlsx file appropriately. According to the scenarios, we are handling each case. For the balancing of CS/ROP part, we have formulated a Linear Program (LP). We are minimizing the maximum difference between the CS/ROP ratio of any two depots/distributors, that is MIN(MAX((CS/ROP)i, (CS/ROP)j)), where i and j span all the depots/distributors in the grid. 

Also we are maximising the total amount of beer transported from the brewery to the depots/distributors in the grid, which was also a part of the problem statement.




