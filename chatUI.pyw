# REFERENCE: "https://platform.openai.com/docs/guides/chat"

import tkinter as tk
import openai
import time

SECRET_KEY = "replace with your OPENAI secret key here"  # 替换你的API key

openai.api_key = SECRET_KEY
ENGINE_LIST = openai.Engine.list()
MODEL_LIST = openai.Model.list()
MAX_TOKEN_LEN = 1024
TIME_OUT = 3

BOT_ROLE = 'assistant'
USER_ROLE = 'user'


# 创建机器人
class MyChatBot:
    def __init__(self) -> None:
        self.messages = []
        self.reset_log()

    def receive_message_from_api(self):
        response = []
        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo-0301',
                messages=self.messages,
                temperature=1.0,
                max_tokens=MAX_TOKEN_LEN,
                top_p=0.6,
                frequency_penalty=2.0,
                presence_penalty=0.0,
                stream=True,
                timeout=TIME_OUT,
            )
        except:
            pass
        return response

    def get_response(self, prompt):
        self.add_user_content(prompt)
        stream_response = self.receive_message_from_api()

        return stream_response

    def reset_log(self):
        self.messages = [{'role': 'system', 'content': f'You are {BOT_ROLE}, a cute catgirl.'}]

    def add_user_content(self, content):
        self.messages.append({'role': USER_ROLE, 'content': content})

    def add_bot_content(self, content):
        self.messages.append({'role': BOT_ROLE, 'content': content})


class ChatUI:
    def __init__(self):
        chatbot = MyChatBot()

        # 创建 GUI 界面
        root = tk.Tk()
        root.title('Chatbot')
        root.attributes("-topmost", True)

        # 创建对话框
        conversation = tk.Text(root, bd=1, bg='white', width=50, height=30)
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

        self.chatbot = chatbot
        self.root = root
        self.conversation = conversation
        self.input_field = input_field

    def clear_conversation(self):
        self.chatbot.reset_log()
        self.conversation.config(state='normal')
        self.conversation.delete('1.0', tk.END)
        self.conversation.config(state='disabled')

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
                    self.conversation.insert(tk.END, "[Timeout In Stream]")
                    self.conversation.see(tk.END)
                    break
                time.sleep(1)

        self.chatbot.add_bot_content(answer)  # 记录机器人的回答
        self.conversation.insert(tk.END, '\n')
        self.conversation.see(tk.END)
        self.conversation.config(state='disabled')


chat_ui = ChatUI()
chat_ui.root.mainloop()
