'''
                                                                                        
                                                                                        
                                                                                        
                                                                                        
                                ██████████████  ██                                      
                              ██              ██  ██                                    
                            ██                    ██                                    
                            ██              ████    ████                                
                            ██      ████████░░░░████    ██                              
                            ██    ██░░░░░░░░░░░░██▒▒▒▒▒▒  ██                            
                              ████░░░░░░░░░░░░░░██▒▒██▒▒  ██                            
                              ██░░░░░░░░░░░░░░░░████  ██  ██                            
                              ██░░░░░░░░░░░░░░░░██    ██  ██                            
                              ██░░░░░░░░░░░░░░░░██    ██  ██                            
                              ██░THE CRAFTSMEN!░██    ██  ██                            
                              ██░░░░░░░░░░░░░░░░████  ██  ██                            
                              ██░░░░░░░░░░░░░░░░██  ██▒▒  ██                            
                              ██░░░░░CHEERS!░░░░██  ▒▒▒▒██                              
                              ██░░░░░░░░░░░░░░░░██▒▒▒▒██                                
                              ██░░░░░░░░░░░░░░░░██████                                  
                            ██  ██░░░░░░░░░░░░░░██                                      
                            ██  ▒▒██████████████▒▒██                                    
                              ██  ▒▒▒▒        ▒▒  ██                                    
                                ████          ████                                      
                                    ██████████      
'''                                                                                   
                                                                                        
                                                                                        
                                                                                        

# necessary imports -->
import cplex
import docplex
import pandas as pd

# inputing the data -->
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

# functions for all the 4 scenarios -->

# for scenario 1 
def apply_scenario_1(start, end):
  
  hub_present = False
  available_to_transport = df_num[start][9]
  rem_for_hub = available_to_transport
  
  for i in range(end - start + 1):
    if df_num[start + i][0] == df_num[start + i][2]:
      hub_present = True

    else:
      if df_num[start + i][3] == 'DIST':
        to_send = df_num[start + i][8]
        rem_for_hub -= to_send
        print("X_" + str(df_num[start + i][0]) + '_to_' + str(df_num[start + i][2]) + '_of_' + str(df_num[start + i][1]) + "=" + str(to_send) + '\n')
        
      else:
        to_send = max(df_num[start + i][6]-df_num[start + i][7],0)
        rem_for_hub -= to_send
        print("X_" + str(df_num[start + i][0]) + '_to_' + str(df_num[start + i][2]) + '_of_' + str(df_num[start + i][1]) + "=" + str(to_send) + '\n')
        
  if hub_present == True:
    print("X_" + str(df_num[start][0]) + '_to_' + str(df_num[start][0]) + '_of_' + str(df_num[start + i][1]) + "=" + str(rem_for_hub) + '\n')

    
# for scenario 2 
def apply_scenario_2(start, end):
  
  available_to_transport = df_num[start][9]
  a_t_t = available_to_transport
  
  from docplex.mp.model import Model
  model_name = 'stock balancing' + str(start)
  m = Model(name = model_name)
  
  decision_variables_transported = []
  total_transported = 0
  
  n_var = 0
  
  for i in range(end - start + 1):
    if df_num[start + i][3] == 'DIST':
      to_send = df_num[start + i][8]
      available_to_transport -= to_send
      print("X_" + str(df_num[start + i][0]) + '_to_' + str(df_num[start + i][2]) + '_of_' + str(df_num[start + i][1]) + "=" + str(to_send) + '\n')
      total_transported += to_send
      continue
      
    name_x = 'X' + '_' + str(df_num[start + i][0]) + '_to_' + str(df_num[start + i][2]) + '_of_' + str(df_num[start + i][1]) 
    decision_variables_transported.append(m.continuous_var(name = name_x))
    total_transported += decision_variables_transported[n_var]
    
    n_var += 1
    
  max_diff = m.continuous_var(name = 'max_diff')
  m.add_constraint(total_transported == a_t_t)
  
  n_var_i = 0
  
  for i in range(end - start + 1):
    if df_num[start + i][3] == 'DIST':
      continue
      
    n_var_j = 0
    
    for j in range(end - start + 1):
      if df_num[start + j][3] == "DIST":
        continue
        
      m.add_constraint((df_num[start + i][7] + decision_variables_transported[n_var_i])/df_num[i + start][5] - (df_num[j + start][7] + decision_variables_transported[n_var_j])/df_num[j + start][5] <= max_diff)
      m.add_constraint(-(df_num[start + i][7] + decision_variables_transported[n_var_i])/df_num[i + start][5] + (df_num[j + start][7] + decision_variables_transported[n_var_j])/df_num[j + start][5] <= max_diff)
      
      n_var_j += 1
      
    n_var_i += 1
    
  m.minimize(max_diff)
  s = m.solve()
  m.print_solution()

  
# for scenario 3
def apply_scenario_3(start, end):
  available_to_transport = df_num[start][9]
  a_t_t = available_to_transport
  
  from docplex.mp.model import Model
  model_name = 'stock balancing' + str(start)
  m = Model(name = model_name)
  
  decision_variables_transported = []
  total_transported = 0
  n_var = 0
  
  for i in range(end - start + 1):
    if df_num[start + i][0] == df_num[start + i][2]:
      to_send = max(df_num[start + i][4]-df_num[start + i][7], 0)
      available_to_transport -= to_send
      print("X_" + str(df_num[start + i][0]) + '_to_' + str(df_num[start + i][2]) + '_of_' + str(df_num[start + i][1]) + "=" + str(to_send) + '\n')
      total_transported += to_send
      continue
      
    name_x = 'X' + '_' + str(df_num[start + i][0]) + '_to_' + str(df_num[start + i][2]) + '_of_' + str(df_num[start + i][1]) 
    decision_variables_transported.append(m.continuous_var(name = name_x))
    total_transported += decision_variables_transported[n_var]
    
    if df_num[start + i][3] == 'DIST':
      m.add_constraint(decision_variables_transported[n_var] <= df_num[start + i][8])
    if df_num[start + i][0]=='PL-1505' and str(df_num[start + i][1])=='88840' and df_num[start + i][2]=='PL-9060':
      m.add_constraint(decision_variables_transported[n_var] == df_num[start + i][8])
    if df_num[start + i][0]=='PL-1505' and str(df_num[start + i][1])=='91864' and df_num[start + i][2]=='PL-9030':
      m.add_constraint(decision_variables_transported[n_var] == df_num[start + i][8])
    n_var += 1
    
  max_diff = m.continuous_var(name = 'max_diff')
  m.add_constraint(total_transported == a_t_t)
  n_var_i = 0
  
  for i in range(end - start + 1):
    if df_num[start + i][0] == df_num[start + i][2]:
      continue
    if df_num[start + i][3] == 'DIST' and df_num[start + i][8]==0:
      n_var_i += 1
      continue
    if df_num[start + i][0]=='PL-1505' and str(df_num[start + i][1])=='88840' and df_num[start + i][2]=='PL-9060':
      n_var_i += 1
      continue
    if df_num[start + i][0]=='PL-1505' and str(df_num[start + i][1])=='91864' and df_num[start + i][2]=='PL-9030':
      n_var_i += 1
      continue
      
    n_var_j = 0
    for j in range(end - start + 1):
      if df_num[start + j][0] == df_num[start + j][2]:
        continue
      if df_num[start + j][3] == 'DIST' and df_num[start + j][8]==0:
        n_var_j += 1
        continue
      if df_num[start + j][0]=='PL-1505' and str(df_num[start + j][1])=='88840' and df_num[start + j][2]=='PL-9060':
        n_var_j += 1
        continue
      if df_num[start + j][0]=='PL-1505' and str(df_num[start + j][1])=='91864' and df_num[start + j][2]=='PL-9030':
        n_var_j += 1
        continue
        
      m.add_constraint((df_num[start + i][7] + decision_variables_transported[n_var_i])/df_num[i + start][5] - (df_num[j + start][7] + decision_variables_transported[n_var_j])/df_num[j + start][5] <= max_diff)
      m.add_constraint(-(df_num[start + i][7] + decision_variables_transported[n_var_i])/df_num[i + start][5] + (df_num[j + start][7] + decision_variables_transported[n_var_j])/df_num[j + start][5] <= max_diff)
      
      n_var_j += 1
    n_var_i += 1
    
  m.minimize(max_diff)
  s = m.solve()
  m.print_solution()


# for scenario 4
def apply_scenario_4(start, end):
  available_to_transport = df_num[start][9]
  a_t_t = available_to_transport
  
  from docplex.mp.model import Model
  model_name = 'stock balancing' + str(start)
  m = Model(name = model_name)
  
  decision_variables_transported = []
  total_transported = 0
  n_var = 0
  
  for i in range(end - start + 1):
    name_x = 'X' + '_' + str(df_num[start + i][0]) + '_to_' + str(df_num[start + i][2]) + '_of_' + str(df_num[start + i][1]) 
    decision_variables_transported.append(m.continuous_var(name = name_x))
    total_transported += decision_variables_transported[n_var]
    
    if df_num[start + i][3] == 'DIST':
      m.add_constraint(decision_variables_transported[n_var] <= df_num[start + i][8])
      
    n_var += 1
    
  max_diff = m.continuous_var(name = 'max_diff')
  m.add_constraint(total_transported == a_t_t)
  
  n_var_i = 0
  for i in range(end - start + 1):
    if df_num[start + i][3] == 'DIST' and df_num[start + i][8]==0:
      n_var_i += 1
      continue
    n_var_j = 0
    for j in range(end - start + 1):
      if df_num[start + j][3] == 'DIST' and df_num[start + j][8]==0:
        n_var_j += 1
        continue
      m.add_constraint((df_num[start + i][7] + decision_variables_transported[n_var_i])/df_num[i + start][5] - (df_num[j + start][7] + decision_variables_transported[n_var_j])/df_num[j + start][5] <= max_diff)
      m.add_constraint(-(df_num[start + i][7] + decision_variables_transported[n_var_i])/df_num[i + start][5] + (df_num[j + start][7] + decision_variables_transported[n_var_j])/df_num[j + start][5] <= max_diff)
      n_var_j += 1
    n_var_i += 1
  m.minimize(max_diff)
  s = m.solve()
  m.print_solution()

  
# looping over the entire data to find out the grids and applying different functions according to the scenarios
curr_SKU = df_num[0][1]
curr_B = df_num[0][0]
to_be_transported = []
start = 0
end = 0

for i in range(len(df_num)):
  if df_num[i][1] == curr_SKU and df_num[i][0] == curr_B:
    end += 1
    
  else:
    if df_num[i-1][10] == 1:
      apply_scenario_1(start, end-1)
      
    elif df_num[i-1][10] == 2:
      apply_scenario_2(start, end-1)
      
    elif df_num[i-1][10] == 3:
      apply_scenario_3(start, end-1)
      
    elif df_num[i-1][10] == 4:
      apply_scenario_4(start, end-1)
      
    end = i + 1
    start = i 
    curr_SKU = df_num[i][1]
    curr_B = df_num[i][0]

if df_num[len(df_num)-1][10] == 1:
  apply_scenario_1(start, end-1)
  
elif df_num[len(df_num)-1][10] == 2:
  apply_scenario_2(start, end-1)
  
elif df_num[len(df_num)-1][10] == 3:
  apply_scenario_3(start, end-1)
  
elif df_num[len(df_num)-1][10] == 4:
  apply_scenario_4(start, end-1)
  
  # - by team - The Craftsmen