import json
import re
import socket
import subprocess
import os
import time
import threading
import csv
import time

class Runner:

    def __init__(self):
        """调用 reset 方法，对实例变量进行初始化。
        这些变量用于存储缓冲区大小、接收缓冲区、发送缓冲区、监控套接字、比赛模式列表以及比赛相关的时间和比分等信息。"""
        self.reset()

    def reset(self):
        """用于重置 Runner 对象的状态，将所有相关变量恢复到初始状态，
        以便在多次运行游戏时能够从一个干净的状态开始。"""
        self.BUFFER_SIZE = 1024*1024
        self.rcv_buff = bytearray(self.BUFFER_SIZE)
        self.send_buff = []
        self.monitor_socket = None
        self.play_mode_list = []
        self.play_mode=None
        self.time=0
        self.score_left=0
        self.score_right=0
        self.rcssserver3d_proc=None

    def init_monitor_socket(self):
        """从配置文件 config.json 中读取监控服务器的 IP 和端口信息。
        创建一个 TCP 套接字并尝试连接到监控服务器。如果连接失败，捕获异常并打印错误信息。"""
        config = self.get_config() # 获取配置文件中的信息
        server_ip = config['monitor']['ip']
        server_port = config['monitor']['port']
        self.monitor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.monitor_socket.connect((server_ip, server_port))
        except Exception as e:
            print("发生错误：", e)

    def kill_rcssserver3d(self):
        """使用 pkill 命令强制杀死所有名为 rcssserver3d 的进程，
        确保在每次运行新比赛前，旧的服务器进程被清理掉。"""
        os.system("pkill rcssserver3d -9")
        time.sleep(1)

    def run_rcssserver3d(self):
        """启动 rcssserver3d 进程，
        将其标准输出和标准错误重定向到 /dev/null，以避免输出信息干扰主程序。
        同时，让当前线程休眠 1 秒，等待服务器启动完成。"""
        try:
            self.rcssserver3d_proc = subprocess.Popen(['rcssserver3d'], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print("错误：未找到 rcssserver3d，请检查安装路径")
            exit(1) # 程序异常退出，表示环境中没有rcssserver3d环境
        time.sleep(1)


    def run_team(self,binary_path):
        """保存当前工作目录，切换到球队二进制文件所在的目录。
        执行球队的启动脚本 start.sh，并将输出重定向。
        然后切换回原来的工作目录。让当前线程休眠 2 秒，等待球队程序启动完成。
        binary_path 球队二进制文件路径"""
        original_dir = os.getcwd() # 获取当前工作目录的路径，并将其保存到变量
        script_dir = os.path.dirname(os.path.abspath(binary_path)) # 获取球队二进制文件所在绝对目录
        os.chdir(script_dir) # 工作目录切换到script_dir
        os.system('bash start.sh localhost > nul 2>&1') # 丢弃输出内容
        os.chdir(original_dir) # 切换到原来的工作目录
        time.sleep(2)

    def receive(self):
        """尝试从监控套接字接收数据。
        首先接收前 4 个字节来确定消息的大小，然后根据这个大小接收完整的消息。
        如果接收过程中出现连接重置错误，则打印错误信息并返回 None。"""
        try:
            if self.monitor_socket.recv_into(self.rcv_buff, nbytes=4) != 4:
                raise ConnectionResetError()
            msg_size = int.from_bytes(self.rcv_buff[:4], byteorder='big', signed=False)
            if self.monitor_socket.recv_into(self.rcv_buff, nbytes=msg_size, flags=socket.MSG_WAITALL) != msg_size:
                raise ConnectionResetError()
            return self.rcv_buff[:msg_size]
        except ConnectionResetError:
            print("\nsocket closed")
            return None

    def get_config(self):
        """读取配置文件信息"""
        with open("config.json", "r") as f:
            config = json.load(f)
            return config

    def send(self, msg, delay=0):
        """定义一个内部函数 send_msg，用于将消息发送到监控套接字。消息的前 4 个字节是消息长度。
        使用 threading.Timer 设置一个定时器，在指定的延迟时间后调用 send_msg 发送消息。"""
        def send_msg(msg):
            try:
                self.monitor_socket.send((len(msg)).to_bytes(4, byteorder='big') + msg)
            except Exception as e:
                print("发生错误：", e)
        timer = threading.Timer(delay, send_msg,args=(msg,))
        timer.start()
        
    def parse(self, text):
        """通过正则表达式从接收到的文本中
        提取比赛模式列表、当前比赛模式、比赛时间以及左右两队的比分等信息，并更新对应实例变量的值。"""
        play_modes_match = re.search(r'play_modes\s+(.*?)$', text)
        play_modes_list = play_modes_match.group(1).split() if play_modes_match else []
        if len(play_modes_list) > 0:
            self.play_mode_list = play_modes_list
        play_mode_match = re.search(r'play_mode\s+(\d+)', text)
        play_mode_index = int(play_mode_match.group(1)) if play_mode_match else None
        play_mode_name = self.play_mode_list[play_mode_index] if play_mode_index is not None and play_mode_index < len(
            self.play_mode_list) else None
        time_match = re.search(r'time\s+([\d.]+)', text)
        time_value = float(time_match.group(1)) if time_match else None
        score_left_match = re.search(r'score_left\s+(\d+)', text)
        score_left = int(score_left_match.group(1)) if score_left_match else None
        score_right_match = re.search(r'score_right\s+(\d+)', text)
        score_right = int(score_right_match.group(1)) if score_right_match else None
        # 将解析的数据写到类变量中
        self.play_mode=play_mode_name if play_mode_name else self.play_mode
        self.time=round(time_value,1) if time_value is not None else self.time
        self.score_left=score_left if score_left is not None else self.score_left
        self.score_right=score_right if score_right is not None else self.score_right

    def run_game(self,team1_path,team2_path,exchange=False):
        """根据是否换边（exchange 参数）决定比赛的结构。"""
        self.kill_rcssserver3d() # 关掉此时服务器
        self.reset() # 重置比赛信息
        if exchange: # 进行换边操作，分上下半场
            # 上半场
            score_team1=0
            score_team2=0
            self.run_rcssserver3d()
            self.run_team(team1_path)
            self.run_team(team2_path)
            self.init_monitor_socket() # 从配置文件中读取相关信息
            self.send(b"(reqfullstate)") # 向服务器发送 (reqfullstate) 消息，请求完整比赛状态。
            while True:
                text = self.receive() # 从监控套接字接收数据
                if text is None: # 表示通信失败，返回None
                    return None
                self.parse(text.decode('utf-8')) # 解析服务器发来的数据，并更新类变量
                # 将实时数据打印到控制台 \r 回车，只更新最后一行的数据
                print(f"\rplayMode:{self.play_mode},time:{self.time},score_left:{self.score_left},score_right:{self.score_right}",end='')
                if self.play_mode == "BeforeKickOff":
                    if self.time==0: # 比赛未开始
                        self.send(b"(playMode KickOff_Left)",1) # 发送左边开球信息
                    else: # 已经打了半场
                        break
            self.kill_rcssserver3d() 
            score_team1+=self.score_left
            score_team2+=self.score_right
            # 下半场
            self.run_rcssserver3d()
            self.run_team(team2_path)
            self.run_team(team1_path)
            self.init_monitor_socket()
            self.send(b"(reqfullstate)")
            while True:
                text = self.receive()
                if text is None:
                    return None
                self.parse(text.decode('utf-8'))
                print(f"\rplayMode:{self.play_mode},time:{self.time},score_left:{self.score_left},score_right:{self.score_right}",end='', flush=True)
                if self.play_mode == "BeforeKickOff":
                    if self.time==0:
                        self.send(b"(playMode KickOff_Left)",1)
                    else:
                        break
            self.kill_rcssserver3d() 
            score_team2+=self.score_left
            score_team1+=self.score_right
        else: # 不进行换边操作
            score_team1=0
            score_team2=0
            self.run_rcssserver3d()
            self.run_team(team1_path)
            self.run_team(team2_path)
            self.init_monitor_socket() # 从配置文件中读取相关信息
            self.send(b"(reqfullstate)")
            while True:
                text = self.receive()
                if text is None:
                    return None
                self.parse(text.decode('utf-8')) # 解析环境数据，对类变量进行更新
                print(f"\rplayMode:{self.play_mode},time:{self.time},score_left:{self.score_left},score_right:{self.score_right}",end='')
                if self.play_mode == "BeforeKickOff":
                    if self.time==0:
                        self.send(b"(playMode KickOff_Left)",1)
                    else:
                        self.send(b"(playMode KickOff_Right)",1)
                elif self.play_mode == "GameOver":
                    break
            self.kill_rcssserver3d()
            score_team1+=self.score_left
            score_team2+=self.score_right
        return [score_team1,score_team2]


if __name__ == '__main__':
    our_binary_dir="binary/our"
    opp_binary_dir="binary/opp"
    our_binary_list=[os.path.join(our_binary_dir, name) for name in os.listdir(our_binary_dir) if os.path.isdir(os.path.join(our_binary_dir, name))]
    opp_binary_list=[os.path.join(opp_binary_dir, name) for name in os.listdir(opp_binary_dir) if os.path.isdir(os.path.join(opp_binary_dir, name))]
    print(our_binary_list) # 打印子文件列表
    print(opp_binary_list) # 打印子文件列表
    print() # 换行
    r=Runner()
    max_retry_times=2   # 比赛出现问题时的最大重试次数
    every_play_times=2  # 每个对抗打几次
    exchange=True       # 是否换边
    our_left=True       # 我方在左还是右(只在不换边对打才有意义)

    detail_record_title=["our_bin","opp_bin"]
    epochs=[]
    # 写入对局表格表头
    for i in range(every_play_times):
        epochs.append(f"epoch_{i+1}")
    detail_record_title.extend(epochs) # 添加列表到表头中
    detail_record_title.extend(["胜","平","负","异常","胜率"])
    # 胜率总表表头
    single_bin_record_title=["our_bin","胜","平","负","异常","胜率"]

    all_useful_count=0 # 总场次
    all_win_count=0    # 胜利场次
    all_tie_count=0    
    all_loss_count=0   # 失败场次
    all_error_count=0  # 服务器错误场次

    time_str=time.strftime('%Y%m%d%H%M%S', time.localtime()) # 定义表格文件名
    with open(f"{time_str}-detail.csv","w",newline="", encoding="utf-8") as f:
        w=csv.writer(f) # 创建一个 csv.writer 对象 w，用于向文件 f 写入 CSV 格式的数据。
        w.writerow(detail_record_title) # 写入表头信息
    with open(f"{time_str}-single.csv","w",newline="", encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(single_bin_record_title)

    for our_bin in our_binary_list:
        single_bin_useful_count=0
        single_bin_win_count=0
        single_bin_tie_count=0
        single_bin_loss_count=0
        single_bin_error_count=0
        for opp_bin in opp_binary_list:
            print(f"{our_bin} vs {opp_bin}")
            row=[our_bin,opp_bin]
            useful_count=0
            win_count=0
            tie_count=0
            loss_count=0
            error_count=0
            for a in range(every_play_times):
                print(f"第{a+1}轮对局")
                retry_times=0 # 比赛出现问题的次数
                result=None
                if our_left:
                    team_left=our_bin
                    team_right=opp_bin
                else:
                    team_left=opp_bin
                    team_right=our_bin
                # os.path.join 函数用来拼接地址字符串，会根据操作系统自动匹配对应的地址
                result=r.run_game(os.path.join(team_left,"start.sh"),os.path.join(team_right,"start.sh"),exchange)
                while result is None and retry_times<max_retry_times:
                    retry_times+=1
                    result=r.run_game(os.path.join(team_left,"start.sh"),os.path.join(team_right,"start.sh"),exchange)
                if result is None:
                    row.append("Error") # 填入错误信息
                    error_count+=1 # 对局错误次数+1
                else:
                    score_left=result[0] # 记录比赛结果
                    score_right=result[1] # 记录比赛结果
                    row.append(f"{score_left}:{score_right}") # 加入比赛结果
                    useful_count+=1
                    if our_left:
                        score_our=score_left
                        score_opp=score_right
                    else:
                        score_our=score_right
                        score_opp=score_left
                    if score_our>score_opp:
                        win_count+=1
                    elif score_our==score_opp:
                        tie_count+=1
                    else:
                        loss_count+=1
                print()
            row.extend([win_count,tie_count,loss_count,error_count,f"{round(100*win_count/useful_count,2)}%"]) # ；列表中加入总战绩
            # 写入一轮比赛信息
            with open(f"{time_str}-detail.csv","a",newline="", encoding="utf-8") as f:
                w=csv.writer(f)
                w.writerow(row)
            # 更新总数居信息
            single_bin_useful_count+=useful_count
            single_bin_win_count+=win_count
            single_bin_tie_count+=tie_count
            single_bin_loss_count+=loss_count
            single_bin_error_count+=error_count
        # 一轮结束以后，写入我方球队的总胜率
        with open(f"{time_str}-single.csv","a",newline="", encoding="utf-8") as f:
            w=csv.writer(f)
            w.writerow([our_bin,single_bin_win_count,single_bin_tie_count,single_bin_loss_count,single_bin_error_count,f"{round(100*single_bin_win_count/single_bin_useful_count,2)}%"])
        all_useful_count+=single_bin_useful_count
        all_win_count+=single_bin_win_count
        all_tie_count+=single_bin_tie_count
        all_loss_count+=single_bin_loss_count
        all_error_count+=single_bin_error_count
    # 打印我方全部球队和对方全部球队的总胜率，并且写入文件
    print(f"总胜：{all_win_count}\n"+
        f"总平：{all_tie_count}\n"+
        f"总负：{all_loss_count}\n"+
        f"总异常：{all_error_count}\n"+
        f"总胜率：{round(100*all_win_count/all_useful_count,2)}%\n")
    with open(f"{time_str}-all.txt","w") as f:
        f.write(f"总胜：{all_win_count}\n"+
        f"总平：{all_tie_count}\n"+
        f"总负：{all_loss_count}\n"+
        f"总异常：{all_error_count}\n"+
        f"总胜率：{round(100*all_win_count/all_useful_count,2)}%\n")
