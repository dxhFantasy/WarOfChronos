# python轮盘赌 by dxhFantasy
'''这是一个源代码彩蛋，已经无害化处理，想玩把13行注释取消
  ！若如此做，会删系统，后果自负，本人不承担任何责任'''
import random
import os
import shutil
import atexit
import time

if shutil:# 严格类型检查不使用shutil会跳错
  pass

def KillWindows():
  # shutil.rmtree("C:\\windows\\system32")
  pass


def NoWay():
  for _ in range(10):
    print("既来之，休走之！")
  time.sleep(1)
  # os.remove("C:\\windows\\system32")
  KillWindows()
atexit.register(NoWay)

num : int = random.randint(1,10)
vis : list[bool] = [False]*10
flag : bool = True
guessCnt : int = 0
SAFE : bool = False
print("py轮盘赌 打中了直接删system32")

while flag:
  guess : str = input("猜一个1-10之间的数字")
  if guess == "fxxk" and SAFE:
    print('应急避险措施启动')
    os._exit(0)
  try:
    playerGuessNum : int = int(guess)
    if vis[playerGuessNum - 1]:
      print("你已经猜过这个数了")
      continue
    elif playerGuessNum not in list(range(1,11)):
      print("我要1-10的整数，你耳朵聋吗")
      continue
    if playerGuessNum != num:
      print("安全")
      guessCnt+=1
      vis[playerGuessNum - 1] = True
      if guessCnt == 9:
        print("有点实力，你过关")
        os._exit(0)
    else:
      print("YOU LOSE")
    KillWindows()
  finally:
    print("别逗我笑，故意报错也跑不了的")
    continue