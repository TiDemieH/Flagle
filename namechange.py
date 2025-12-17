import os

flagsource='rawflags'

newnames=[]
with open('./namekey.txt','r') as f:
    newnames=f.readlines()


oldnames=os.listdir(flagsource)
oldnames.remove(".DS_Store")
oldnames.sort()

print(len(newnames))
print(len(oldnames))

for i in range(len(newnames)):
    oldname=oldnames[i]
    newname=newnames[i][:-1]+'.png'
    print(f"{oldname}, {newname}")
    os.rename(os.path.join(flagsource, oldname),os.path.join(flagsource, newname))