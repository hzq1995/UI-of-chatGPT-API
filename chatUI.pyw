# REFERENCE: "https://platform.openai.com/docs/guides/chat"

import time
import openai
import threading
import tkinter as tk

SECRET_KEY = "replace your OPENAI secret key here"  # 替换你的API key
openai.api_key = SECRET_KEY

MAX_TOKEN_LEN = 1024
TIME_OUT = 3

BOT_ROLE = 'assistant'
USER_ROLE = 'user'
PROMPT = f'you are {BOT_ROLE}, a cute catgirl.'  # 定制AI的性格


# 超时装饰器
def timeout(seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = [None]
            def worker():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    pass
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            t.join(seconds)
            if t.is_alive():
                return []
            return result[0]
        return wrapper
    return decorator


# 创建机器人
class MyChatBot:
    def __init__(self) -> None:
        self.messages = []
        self.reset_log()

    @timeout(TIME_OUT)
    def receive_message_from_api(self):
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo-0301',
            messages=self.messages,
            temperature=1.0,
            max_tokens=MAX_TOKEN_LEN,
            top_p=0.6,
            frequency_penalty=2.0,  # 降低出现频繁的单词的权重
            presence_penalty=0.0,  # 降低不常出现的单词的权重
            stream=True,
            timeout=TIME_OUT,
        )
        return response

    def get_response(self, prompt):
        self.add_user_content(prompt)
        stream_response = self.receive_message_from_api()

        return stream_response

    def reset_log(self):
        self.messages = [{'role': 'system', 'content': PROMPT}]

    def add_user_content(self, content):
        self.messages.append({'role': USER_ROLE, 'content': content})

    def add_bot_content(self, content):
        self.messages.append({'role': BOT_ROLE, 'content': content})


class ChatUI:
    def __init__(self):
        chatbot = MyChatBot()

        self.is_paused = False

        # 创建 GUI 界面
        root = tk.Tk()
        root.title('Chatbot')
        root.attributes("-topmost", True)

        # 创建对话框
        conversation = tk.Text(root, bd=1, bg='white', width=60, height=50)
        conversation.config(state='disabled')
        conversation.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # 创建输入框
        input_field = tk.Entry(root, width=50)
        input_field.bind("<Return>", (lambda event: self.chatting()))  # 使用回车发送
        input_field.grid(row=1, column=0, sticky='nsew', padx=5)

        # 创建发送按钮
        send_button = tk.Button(root, text='Send', command=self.chatting)  # 点击发送
        send_button.grid(row=1, column=1, sticky='nsew', padx=5)

        # 创建清除对话按钮
        clear_button = tk.Button(root, text='Clear', command=self.clear_conversation)  # 点击发送
        clear_button.grid(row=0, column=1, sticky='nsew', padx=5)

        # 创建暂停按钮
        pause_button = tk.Button(root, text='Pause', command=self.pause_chat)
        pause_button.grid(row=2, column=0, sticky='nsew', padx=5)

        self.chatbot = chatbot
        self.root = root
        self.conversation = conversation
        self.input_field = input_field
        self.pause_button = pause_button

    def pause_chat(self):
        self.is_paused = not self.is_paused  # 切换状态

    def chatting(self):
        if not self.input_field.get():  # 如果输入框为空，则直接返回
            return

        if self.is_paused:  # 如果被暂停，则直接显示提示信息
            if self.input_field.get() == 'resume':  # 如果输入的是'resume'，则恢复聊天状态，并清空输入框
                self.is_paused = False
                self.update_conversation("Chatbot is resumed.", True)
                self.input_field.delete(0, tk.END)
            else:
                message = "Chatbot is paused. Type 'resume' to continue."
                self.update_conversation(message)
                return
            user_input = self.input_field.get()
            self.update_conversation(user_input)

            response = self.chatbot.get_response(user_input)
            self.update_conversation(response, True)

            self.input_field.delete(0, tk.END)

    def update_conversation(self, message, is_bot=False):
            if is_bot:
                message = f"Bot: {message}"
            else:
                message = f"You: {message}"

            self.conversation.config(state='normal')
            self.conversation.insert(tk.END, message + '\n')
            self.conversation.see(tk.END)
            self.conversation.config(state='disabled')

    def clear_conversation(self):
            self.conversation.config(state='normal')
            self.conversation.delete(1.0, tk.END)
            self.conversation.config(state='disabled')

    def pause_chat(self):
        self.is_paused = not self.is_paused  # 切换状态
        if self.is_paused:
            self.update_conversation("Chatbot is paused. Type 'resume' to continue.")
        else:
            self.update_conversation("Chatbot is resumed.")

    # 定义获取响应的函数
    def chatting(self):

        self.conversation.config(state='normal')
        input_text = self.input_field.get()
        self.conversation.insert(tk.END, "You: " + input_text + '\n')
        self.conversation.see(tk.END)

        self.input_field.delete(0, tk.END)  # 清空输入bar
        self.input_field.update()

        self.conversation.insert(tk.END, "Bot: ")  # 开始导出回答
        stream_response = self.chatbot.get_response(input_text)
        answer = ""
        timeout_cnt = 0
        while True:  # 连续获取stream，并保存最终的answer
            try:
                package = next(stream_response)
                if hasattr(package.choices[0].delta, 'role'):
                    continue
                single_token = package.choices[0].delta.content

                self.conversation.insert(tk.END, single_token)
                self.conversation.see(tk.END)
                self.conversation.update()

                answer += single_token
                if package.choices[0].finish_reason == "stop":
                    break
            except:
                if len(answer) > 0:
                    break
                timeout_cnt += 1
                if timeout_cnt >= TIME_OUT:
                    self.conversation.insert(tk.END, "[Timeout]")
                    self.conversation.see(tk.END)
                    break
                time.sleep(1)

        self.chatbot.add_bot_content(answer)  # 记录机器人的回答
        self.conversation.insert(tk.END, '\n')
        self.conversation.see(tk.END)
        self.conversation.config(state='disabled')


chat_ui = ChatUI()
chat_ui.root.mainloop()
