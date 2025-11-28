# -*- coding: utf-8 -*-
import copy
from email.mime import image
import json
from logging import root
import math
import shutil
import tkinter as tk
import os
from tkinter import END, MULTIPLE, Button, IntVar, PhotoImage, StringVar, filedialog
import zipfile
import pydub
import time

print('''
#以下是说明!!!!
#本程序用于将多个mcz谱面合并为一个mcz谱面
#合并时可自定义各谱面间的休息段时长
#合并后谱面信息为手动输入
#文件直接导出到当前目录下final_output.mcz

#以下是注意!!!!
#依赖pydub库和ffmpeg，请确保已安装，ffmpeg要求加入环境变量（可以试试目录中的bat脚本）
#mcz文件不能有子目录且只能含一个ogg文件和一个.mc文件和一个jpg文件
#文件名除了扩展名的部分不能含"."
#mcz文件必须直接包含.ogg .mc .jpg/.png文件，不能有子目录
#谱面保留流速变化和效果，所以合成后的谱面流速受bpm影响，如需流速均匀请自行在bpmlist中添加effect或者打开const
#偏移尽量准确（否则会有谱面音乐不同步）
#仅支持使用malody制谱器制作的mcz文件
#如果音频留白较长，适当裁剪ogg前段
    ''')

songlist=[] #存储mcz目录
songfilenamelist=[] #存储mcz文件名(无后缀)
sortedsongfilenamelist=[] #存储排序后的mcz文件名(输出带序号的歌曲名)
order=[] #存储输入的顺序{目录:序号}
background=("./sample.jpg") #默认背景图片

#列表标序函数
def SetSorter(set):
    for i in range(len(set)):
        set[i]=f"{i+1}"+"."+set[i]
    return set
    print("谱面排序完毕！")



def main():
    print("选择文件中......")
    FileSelector()
    SortSongs()
    GetInfo()


#文件选择窗口
def FileSelector():
    #存储选择的文件路径
    global SelectedFilePaths
    SelectedFilePaths=filedialog.askopenfilename(
        title="select a mcz files",
        filetypes=[("map","*.zip *.mcz")],
        multiple=True)
    print("文件选择完毕！")

#获取背景图片函数
def Getbg():
    global background
    background=filedialog.askopenfilename(
        title="select a mcz files",
        filetypes=[("background","*.jpg *.png")],
        multiple=False)
    print("背景选择完毕！")

#获取标序的歌曲名函数
def SortSongs():

    #新元素加入songlist
    for file in range(len(SelectedFilePaths)):
        songlist.append(SelectedFilePaths[file])
        songfilenamelist.append(os.path.basename(SelectedFilePaths[file])[0:-4])

    #对songfilenamelist排序并存入sortedsongfilenamelist
    sortedsongfilenamelist=SetSorter(songfilenamelist)

    #songlist换行为songtext字符串变量
    songtext.set("selected maps:\n"+"\n".join(sortedsongfilenamelist))

    #修改文件选择按钮状态
    FileSelectorButton.config(text="files selected",state="disabled")
    print("谱面排序完毕！")

#获取输入顺序,休息段时长,函数
def GetInfo():
    #创建输入顺序标签和输入框,获取输入顺序
    EntryTip=tk.Label(root,text="input the order of the songs\nFormat:1 2 3...n-1 n",)
    EntryTip.place(x=0,y=90)
    global OrderEntry,RestEntry,CreatorEntry,TitleEntry,VersionEntry
    OrderEntry=tk.Entry(root)
    OrderEntry.place(width=100,x=0,y=130)
    GetOrderButton=tk.Button(
        root, 
        text="confirm", 
        command=ConfirmOrder)
    GetOrderButton.place(x=110,y=130)

    #创建输入休息段时长标签和输入框,获取休息段时长参数
    RestTip=tk.Label(root,text="input the rest time(int)")
    RestTip.place(x=0,y=150)
    RestEntry=tk.Entry(root)
    RestEntry.place(width=100,x=0,y=170)
    GetRestButton=tk.Button(
        root, 
        text="confirm", 
        command=ConfirmRest)
    GetRestButton.place(x=110,y=170)

    #创建输入制作者标签和输入框,获取制作者
    CreatorTip=tk.Label(root,text="input title")
    CreatorTip.place(x=0,y=190)
    CreatorEntry=tk.Entry(root)
    CreatorEntry.place(width=100,x=0,y=210)
    GetCreatorButton=tk.Button(
        root, 
        text="confirm", 
        command=ConfirmCreator)
    GetCreatorButton.place(x=110,y=210)


    #创建输入标题标签和输入框,获取标题
    TitleTip=tk.Label(root,text="input creator")
    TitleTip.place(x=0,y=230)
    TitleEntry=tk.Entry(root)
    TitleEntry.place(width=100,x=0,y=250)
    GetTitleButton=tk.Button(
        root, 
        text="confirm", 
        command=ConfirmTitle)
    GetTitleButton.place(x=110,y=250)

    #创建输入版本标签和输入框，获取版本
    VersionTip=tk.Label(root,text="input version")
    VersionTip.place(x=0,y=270)
    VersionEntry=tk.Entry(root)
    VersionEntry.place(width=100,x=0,y=290)
    GetVersionButton=tk.Button(
        root, 
        text="confirm", 
        command=ConfirmVersion)
    GetVersionButton.place(x=110,y=290)

def ConfirmVersion():
    global version,versionconfirmed
    version=VersionEntry.get()
    versionconfirmed.set(1)
    UnlockStartButton()
    print("版本确认完毕！")

#按钮确认输入制作者
def ConfirmCreator():
    global creator,creatorconfirmed
    creator=CreatorEntry.get()
    creatorconfirmed.set(1)
    UnlockStartButton()
    print("作者确认完毕！")

#按钮确认输入标题
def ConfirmTitle():
    global title,titleconfirmed
    title=TitleEntry.get()
    titleconfirmed.set(1)
    UnlockStartButton()
    print("标题确认完毕！")

#按钮确认输入顺序
def ConfirmOrder():
    global order,songlist,orderdict,orderconfirmed
    temporder=OrderEntry.get()
    order=temporder.split(" ")
    for i in range(len(songlist)):
        order[i]=int(order[i])
    orderdict=dict(zip(songlist,order)) #存储顺序字典
    orderconfirmed.set(1)
    UnlockStartButton()

#按钮确认休息段时长
def ConfirmRest():
    global rest,restconfirmed #存储休息段时长
    rest=int(RestEntry.get())
    restconfirmed.set(1)
    UnlockStartButton()
    print("休息段时长确认完毕！")

#解锁start按钮
def UnlockStartButton():
    global StartButton,orderconfirmed,restconfirmed,titleconfirmed,creatorconfirmed
    if orderconfirmed.get()==1 and restconfirmed.get()==1 and creatorconfirmed.get()==1 and titleconfirmed.get()==1 and versionconfirmed.get()==1:
        StartButton.config(state="normal")
        print("所有参数确认完毕，开始按钮已解锁！")


#创建并解压mcz到临时目录并重命名
def UnzipFile():
    print("文件解压中......")
    if os.path.exists("./temp"):
        shutil.rmtree("./temp")
    if os.path.exists("./output"):
        shutil.rmtree("./output")

    try:
        print("创建临时文件夹中......")
        for file in range(len(songlist)):
            #按序号创建临时文件夹
            os.makedirs(f"./temp/{orderdict[songlist[file]]}")

            #解压mcz文件到对应临时文件夹
            with zipfile.ZipFile(songlist[file],"r") as mczfile:
                mczfile.extractall(f"./temp/{orderdict[songlist[file]]}")
        
        print("文件解压完毕，正在重命名文件并转换格式......")
        #按序号重命名解压后的文件
        for filepath,dirnames,filenames in os.walk("./temp"):
            for filename in filenames:
                tempname=os.path.join(filepath,filename)
                dirname,filename=os.path.split(tempname)
                tempsplit=filename.split(".")#文件名不能含"."和"/" 分割文件名和后缀
                tempdirsplit=dirname.split("\\")#目录名分割
                tempsplit[0]=f"{tempdirsplit[-1]}"
                combinedname=dirname+"/"+tempsplit[0]+"."+tempsplit[1]
                #重命名
                oldname=tempname
                newname=combinedname
                os.rename(oldname,newname)
                #转换mp3为ogg
                if "mp3" in tempsplit[1]:   
                    print("转换mp3到ogg......")
                    sound=pydub.AudioSegment.from_mp3(newname)
                    sound.export(newname[0:-3]+"ogg",format="ogg")
                    os.remove(newname)
        print("文件重命名完毕！")       
        os.mkdir("./output")
        shutil.copy(background,"./output")
    except zipfile.BadZipFile:
        print("bad mcz file")
    except PermissionError:
        print("Permission Denied")
    except Exception as e:
        print(f"Error:{e}")

#读取ogg文件函数
def OggReader():
    print("读取ogg文件中......")
    global oggdict
    #元素为ogg文件
    oggdict={}
    for i in order:
        oggdict[i]=pydub.AudioSegment.from_ogg(f"./temp/{i}/{i}.ogg")

#读取json并裁切ogg文件函数
def JsonAndOggHandle():
    mapdict={}
    songlengthdict={}
    timelist=[]
    note=[]
    songstotallength=0
    endposition=0
    m=0
    originalmapdict={}
    offsetdict={}
    effectlist=[]

    #初始化
    for i in order:
        #.mc文件存储到mapdict中
        mapdict[i]=json.load(open(f"./temp/{i}/{i}.mc",encoding="utf-8"))
        originalmapdict[i]=copy.deepcopy(mapdict[i])#静态深拷贝原始mapdict
        #ogg文件开头添加偏移段
        print("ogg文件偏移修改中......")
        if "offset" in mapdict[i]["note"][-1]:
            offsetdict[i]=mapdict[i]["note"][-1]["offset"]
        else:
            offsetdict[i]=0
        if offsetdict[i] >= 0:
            oggdict[i]=pydub.AudioSegment.silent(duration=offsetdict[i])+oggdict[i]
        else:
            oggdict[i]=oggdict[i][-(len(oggdict[i])+offsetdict[i]):]
        oggdict[i].export(f"./temp/{i}/{i}.ogg",format="ogg")
        oggdict[i]=pydub.AudioSegment.from_ogg(f"./temp/{i}/{i}.ogg")
        #ogg长度存储到songlengthdict中（单位为ms）
        songlengthdict[i]=len(oggdict[i])
    #遍历所有.mc/.ogg文件 
    
    
    for j in range(len(songlist)):
        m+=1 #循环次数计数
        #重构timelist
        print("正在合成新的bpmlist......")
        for n in range(len(mapdict[j+1]["time"])):
            if m==1:
                timelist.append(mapdict[j+1]["time"][n])
                timelist[-1]["delay"]=0
            else:
                mapdict[j+1]["time"][n]["beat"][0]+=(songstotallength+rest*(m-1))
                timelist.append(mapdict[j+1]["time"][n])
                timelist[-1]["delay"]=0

        #重构effect
        print("正在合成新的effectlist......")
        if "effect" in mapdict[j+1]:
            for n in range(len(mapdict[j+1]["effect"])):
               if m==1:
                   effectlist.append(mapdict[j+1]["effect"][n])
               else:
                   mapdict[j+1]["effect"][n]["beat"][0]+=(songstotallength+rest*(m-1))
                   effectlist.append(mapdict[j+1]["effect"][n])


        
        #重构note
        print("正在排列note......")
        currentnotes=mapdict[j+1]["note"]

        if m==1:#第一首
            note+=currentnotes
            del note[-1]
            print("第一首note排列完毕")

        elif m!= len(order):#不是最后一首
            for notes in range(len(currentnotes)):
                if "endbeat" in currentnotes[notes]:
                    mapdict[j+1]["note"][notes]["beat"][0]+=(songstotallength+rest*(m-1))
                    mapdict[j+1]["note"][notes]["endbeat"][0]+=(songstotallength+rest*(m-1))
                else:
                    mapdict[j+1]["note"][notes]["beat"][0]+=(songstotallength+rest*(m-1))
            note+=mapdict[j+1]["note"]
            del note[-1]
            print(f"第{m}首note排列完毕")

        else:#最后一首
            for notes in range(len(currentnotes)):
                if "endbeat" in currentnotes[notes]:
                    mapdict[j+1]["note"][notes]["beat"][0]+=(songstotallength+rest*(m-1))
                    mapdict[j+1]["note"][notes]["endbeat"][0]+=(songstotallength+rest*(m-1))
                else:
                    mapdict[j+1]["note"][notes]["beat"][0]+=(songstotallength+rest*(m-1))
            note+=mapdict[j+1]["note"]
            note[-1]={"beat": [0,0,1],"type": 1,"sound": "mergedogg.ogg","offset": 0}
            print("最后一首note排列完毕")

        #计算裁切位置
        print(f"正在调整第{m}个ogg结尾偏移......")
        t=0
        temppositionpdict={}#存放变速位置列表（元素为列表）
        position={}#存放变速位置
        tempbpmdict={}#存放变速bpm列表
        #遍历第j+1个.mc文件的timelist
        for k in range(len(mapdict[j+1]["time"])):
            temppositionpdict[k]=originalmapdict[j+1]["time"][k]["beat"]
            position[k]=temppositionpdict[k][0]+(temppositionpdict[k][1]/temppositionpdict[k][2])
            tempbpmdict[k]=mapdict[j+1]["time"][k]["bpm"]
        #计算前段时间
        for l in range(len(position)-1):
            tempt=60000*((position[l+1]-position[l])/tempbpmdict[l])
            t+=tempt #已确定结束位置的时间t
        #计算结尾时间差并添加空白段
        T=songlengthdict[j+1]-t #T=Δt #包含最后一段和裁切段
        endposition=math.ceil((T*tempbpmdict[len(position)-1])/60000+position[len(position)-1])
        realendposition=(T*tempbpmdict[len(position)-1])/60000+position[len(position)-1]
        deltaposition=endposition-realendposition#要裁切的位置差值
        tappend=deltaposition*60000/tempbpmdict[len(position)-1]#要保留的时间差值
        appendogg=oggdict[j+1]+pydub.AudioSegment.silent(duration=tappend)
        appendogg.export(f"./temp/{j+1}/{j+1}.ogg",format="ogg")
        oggdict[j+1]=pydub.AudioSegment.from_ogg(f"./temp/{j+1}/{j+1}.ogg")
        print(f"第{m}个ogg结尾偏移调整完毕!")
        #加上歌曲长度
        songstotallength+=endposition
        #加上休息段长度
        print(f"添加第{m}个休息段")
        if m!=len(order) and rest!=0: 
            timelist.append({"beat":[songstotallength+rest*(m-1),0,1],"bpm":60,"delay":0})
    print("所有ogg文件偏移调整完毕！")
    print("正在生成合并后的.mc文件......")
    mcfile={
        "meta":{"id":0,
                    "creator":creator,
                    "background":os.path.basename(background),
                    "cover":"",
                    "version":version,
                    "mode":0,
                    "song":{"title":title,
                            "artist":"Various Artists",
                            "file":"mergedogg.ogg",
                            "bpm":60},
                    "mode_ext":{"column":4,
                                    "bar_begin":0},
                    "aimode":""},
        "time":timelist,
        "effect":effectlist,
        "note":note,
        "extra":None,
            }
    with open("./output/merged.mc", "w", encoding="utf-8") as f:
        json.dump(mcfile, f, ensure_ascii=False,indent=None, separators=(',', ':'))
    print(".mc文件生成完毕！")
#合并ogg文件函数
def OggMerger():
    print("开始合并ogg文件......")
    ogglist=[]
    try:
        for j in range(len(songlist)):
            print(f"正在合并第{j+1}个ogg文件......")
            ogglist.append(oggdict[j+1])
            print(f"第{j+1}个ogg文件合并完毕！")
            print(f"正在添加第{j+1}个休息段......")
            ogglist.append(pydub.AudioSegment.silent(duration=rest*1000))
        print("合成完整ogg文件中......")
        mergedogg=sum(ogglist)
        mergedogg.export("./output/mergedogg.ogg",format="ogg")
        print("所有ogg文件合并完毕！")
    except FileNotFoundError:
        print("file not found")
    except Exception as e:
        print(f"Error:{e}")


#导出文件函数
def OutPutResult():
    print("正在导出最终文件......")
    with zipfile.ZipFile("./final_output.mcz","w") as outputmcz:
        outputmcz.write("./output/merged.mc",arcname="merged.mc")
        outputmcz.write("./output/mergedogg.ogg",arcname="mergedogg.ogg")
        outputmcz.write("./output/"+os.path.basename(background),arcname=os.path.basename(background))
    print("文件导出完毕！")
    # #修改temp中json文件内容（调试用）
    # for i in range(len(songlist)):
    #     mcdata = json.load(open(f"./temp/{i+1}/{i+1}.mc",encoding="utf-8"))
    #     if mcdata["meta"]["background"][-2]=="p":
    #         mcdata["meta"]["background"]=f"{i+1}.jpg"
    #     else:
    #         mcdata["meta"]["background"]=f"{i+1}.png"
    #     mcdata["note"][-1]["sound"]=f"{i+1}.ogg" 
    #     mcdata["note"][-1]["effect"]=0
    #     json.dump(mcdata, open(f"./temp/{i+1}/{i+1}.mc", "w"), ensure_ascii=False, indent=None, separators=(',', ':'))


            

def Start():
    starttime=time.time()
    UnzipFile()
    OggReader()
    JsonAndOggHandle()
    OggMerger()
    OutPutResult()
    endtime=time.time()
    print("全部操作完成！请在当前目录下查看final_output.mcz文件！并在关闭程序后手动清除temp和output文件夹")
    print(f"总用时：{endtime-starttime}秒")



#主窗口定义
root = tk.Tk()
root.title("mcz map merger")
root.geometry("600x400")

#定义songtext变量，rest变量
songtext=tk.StringVar()
orderconfirmed=tk.IntVar()
restconfirmed=tk.IntVar()
creatorconfirmed=tk.IntVar()
titleconfirmed=tk.IntVar()
versionconfirmed=tk.IntVar()
versionconfirmed.set(0)
titleconfirmed.set(0)
orderconfirmed.set(0)
restconfirmed.set(0)
creatorconfirmed.set(0)

#显示信息
InfoLabel=tk.Label(
    root,
    text="mcz map merger v1.0\nby NENENEKO\nspecial thanks to DouBao,Deepseek,Copilot,RMAILtF930\nBUGreport: QQ:3125998062 Bilibili:UID:348016585",
    justify="left")
InfoLabel.place(x=70,y=325)

#放置图片
PhotoImage=tk.PhotoImage(file="./avatar.ppm")
ImageLabel=tk.Label(
    root,
    image=PhotoImage)
ImageLabel.place(x=0,y=330)


#定义文件选择框按钮
FileSelectorButton=tk.Button(
    root,
    text="click to choose files",
    command=main,
    bg="#959cff")
FileSelectorButton.place(width=150,height=40,x=0,y=0)

#定义开始按钮
StartButton=tk.Button(
    root,
    state="disabled",
    text="START",
    command=Start,
    bg="#959cff")
StartButton.place(width=150,height=40,x=0,y=40)

#输出songlist标签
SonglistLabel=tk.Label(
    root,
    textvariable=songtext,
    justify="left")
SonglistLabel.place(x=400,y=0)

#选择背景按钮
GetBackgroundButton=tk.Button(
    root,
    text="select bg",
    command=Getbg,
    bg="#959cff")
GetBackgroundButton.place(width=150,height=40,x=200,y=0)

root.mainloop()