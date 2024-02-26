f = open("/home/cmj.gcp.3/zzimkong-modeling/nerfstudio/data/1708914885510/colmap_result.txt", 'r')
line = f.readline()
f.close()

print(line.split(']')[-1])