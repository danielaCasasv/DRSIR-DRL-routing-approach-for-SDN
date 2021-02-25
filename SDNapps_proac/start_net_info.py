import pandas as pd
file = '/home/controlador/ryu/ryu/app/SDNapps_proac/net_info.csv'
df = pd.read_csv(file)
df.delay = 0
df.pkloss = 0

print df