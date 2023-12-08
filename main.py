import discord
from discord import app_commands
import os
#from discord.ext import commands

import gspread
from oauth2client.service_account import ServiceAccountCredentials

#BOTのトークン
#書き込み先のスプレッドシートキーを追加
# システム環境変数からSPREADSHEET_KEYとTOKENを読み込む
SPREADSHEET_KEY = os.getenv("SPREADSHEET_KEY")
print(SPREADSHEET_KEY)
TOKEN = os.getenv("TOKEN")
print(TOKEN)

#DiscordBot関係の初期設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

#gspreadの初期設定
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

#ダウンロードしたjsonファイルをドライブにアップデートした際のパス
json = 'discordbot-399616-1efb0c1c2a2b.json'

credentials = ServiceAccountCredentials.from_json_keyfile_name(json, scope)

gc = gspread.authorize(credentials)

#共有設定したスプレッドシートの1枚目のシートを開く
worksheet = gc.open_by_key(SPREADSHEET_KEY).worksheet('単語帳')

# Create a subroutine to load the name and explanation data from the Google Sheets spreadsheet
def load_dictionary_data():
    global name_list
    global exp_list
    global dic_data
    global worksheet

    # Name and explanation data
    name_list = worksheet.col_values(1)
    exp_list = worksheet.col_values(2)

    # Convert the lists to a dictionary
    dic_data = {k: v for k, v in zip(name_list, exp_list)}

# Initial loading of dictionary data
load_dictionary_data()

# ファイル名と初期の per_list
#PER_LIST_FILE = "per_list.txt" #本番
PER_LIST_FILE = "per_list_test.txt" #テスト用
per_list = []

# ファイルから per_list を読み込む関数
def load_per_list():
    try:
        with open(PER_LIST_FILE, "r") as file:
            per_list = [int(line.strip()) for line in file.readlines()]
    except FileNotFoundError:
        per_list = []
    return per_list

# per_list をファイルに保存する関数
def save_per_list():
    with open(PER_LIST_FILE, "w") as file:
        for channel_id in per_list:
            file.write(str(channel_id) + "\n")

        
###イベント

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    global per_list
    per_list = load_per_list()  # 起動時に per_list を読み込む

@client.event
async def on_message(message):
    global name_list
    global exp_list
    global dic_data
    global worksheet
    global per_list
    
    if message.author == client.user:
        return
    
    # mount
    if message.content.startswith('$mount'):
        if message.channel.id not in per_list:
            per_list.append(message.channel.id)
            save_per_list()  # per_list をファイルに保存
            await message.channel.send(f'[{message.channel.name}]が登録されました')
        else:
            await message.channel.send(f'[{message.channel.name}]はすでに登録されています')
        print(per_list)

    # unmount
    if message.content.startswith('$unmount'):
        if message.channel.id in per_list:
            per_list.remove(message.channel.id)
            save_per_list()  # per_list をファイルに保存
            await message.channel.send(f'[{message.channel.name}]の登録が解除されました')
        else:
            await message.channel.send(f'[{message.channel.name}]は登録されていません')
        print(per_list)

    #登録されたCHのみで反応
    if message.channel.id not in per_list:
        return
    
    print(f'{message.guild.name}@[{message.channel.name}] {message.author.name}:{message.content}')

    #辞書
    if message.content in dic_data.keys():
        print(dic_data[message.content])
        await message.channel.send(f'\n**【{message.content}】**\n> {dic_data[message.content]}')
    
    # 部分一致辞書検索
    if message.content.startswith('?'):
        keyword = message.content[1:]  # 先頭の?を除去
        matched_items = [(k, v) for k, v in dic_data.items() if keyword in k]
        response = ''
        for i, (k, v) in enumerate(matched_items[:5]):  # 最初の5つだけ表示
            response += f'\n**{i+1}. 【{k}】**\n> {v}\n'
        if len(matched_items) > 5:
            response += f'\n  他にも{len(matched_items)-5}件見つかりました。'
        if response:  # make sure the response is not empty
            await message.channel.send(response)
            print(response)
        else:
            await message.channel.send('マッチしませんでした:'+keyword)
            print('マッチしませんでした:'+keyword)
        

    #辞書リロード
    if message.content.startswith('$reload'):
        print('辞書リロード')
        load_dictionary_data()
        await message.channel.send('辞書を読み込み直しました')
        #print(dic_data)

    # アナウンス機能
    if message.content.startswith('$announce '):
        announcement = message.content[len('$announce '):]  # 先頭の$announce を除去
        for channel_id in per_list:
            channel = client.get_channel(channel_id)
            await channel.send(announcement)

    
client.run(TOKEN)
