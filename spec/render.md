@Erytheia
(Pumila)
render を使った Discord Bot の構築と運用（無料）
Python
bot
render
discord
discord.py
最終更新日 2023年06月11日
投稿日 2023年04月09日
はじめに
無料で使えるホスティングサービスである Render と Discord.pyを用いた、Discord Bot の構築と運用についてまとめてみました。

Render とは
Render とは、ウェブサイトやアプリケーションをホストするためのクラウドホスティングサービスです。静的サイト、Docker コンテナ、サーバーレス関数、データベース、バックエンド API など、さまざまな種類のアプリケーションをホスティングできます。いわゆる PaaS（Platform as a Service）と呼ばれるサービスに分類されます。また、GitHub などと連携することで、簡単にソースコードのデプロイができます。主な対応言語として、Node.js, Python, Ruby, Elixir, Go, Rust などがあります。
Render には、無料枠があるため、個人開発者や小規模のプロジェクトにも利用しやすくなっています。また従量課金制であり、トラフィックやリソースの使用量に応じて課金されます。さらに、Render は高速かつ安全な CDN（コンテンツ配信ネットワーク）を提供しているため、世界中のユーザーに高速で安定したアプリケーションの提供が可能です。

環境
Raspberry Pi 4 Model B
CentOS Stream 8
Python 3.11.0
discord.py 2.1.1
Render
Uptime Robot
導入
Bot アカウントの作成
Discord Developer Portal より Bot アカウントを作成しましょう。詳細な手順については既にまとまっている記事があるため省きます。以下の記事を参考にして下さい。
実装においてアクセストークンが必要になります。メモしておきましょう。



Render アカウントの作成
Render にアクセスし、[GET STARTED FOR FREE] をクリックします。
キャプチャ.PNG
GitHub 連携ができるので、GitHub 連携を連携して下さい。Render by Render would like permission to:と表示されるので、Authorize Render を選択して下さい。その後、メールアドレス認証が求められるのでメールアドレスを入力し、[COMPLETE SIGN UP] を選択して下さい。
キャプチャ.PNG
Activate your Render account というメールが届くのでリンクを踏んで認証して下さい。これでアカウント作成完了です。
今回使用するのは Web Services になります。性能は以下の通りです。かなりしょぼいですね。稼働時間にも制限があり Bot も一つまでしか運用できません。

0.1 CPU
512 MB の RAM
月当たり 750 時間の稼働時間
100 GB のアウトバウンド
また、この Web Services では15分レスポンスがないと自動的にダウンしてしまいます。そこで、Bot とは別に Web サーバを立ち上げ、Uptime Robot を用いて、定期的にレスポンスを送ることにします。

Web Services on the free instance type are automatically spun down after 15 minutes of inactivity. When a new request for a free service comes in, Render spins it up again so it can process the request.



また、Render では GitHub のリポジトリに変更があった場合、自動的に再デプロイしてくれる機能があります。

デプロイ
アカウントの準備ができたのでいよいよデプロイに移っていきます。必要なファイルを GitHub のリポジトリに追加します。必要なファイルは main.py, keep_alive.py, requirements.txt, Dockerfile になります。一例として、投稿されたメッセージに自動的にリアクションする Bot を考えてみましょう。各々動かした Bot のソースコードに置き換えてください。keep_alive() で Web サーバを立ち上げています。

main.py
import discord
import os
from keep_alive import keep_alive

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print('ログインしました')

@client.event
async def on_message(message):
    emoji ="👍"
    await message.add_reaction(emoji)

TOKEN = os.getenv("DISCORD_TOKEN")
# Web サーバの立ち上げ
keep_alive()
client.run(TOKEN)
続いて keep_alive.py ファイルになります。Flask を用いて Web サーバを立ち上げています。

keep_alive.py
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
requirements.txt ファイルについては pip freeze コマンドより必要なライブラリを記載して下さい。

requirements.txt
discord.py==2.1.1
Flask==2.2.3
最後に Dockerfile になります。以下のように作成して下さい。

Dockerfile
FROM python:3.11
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
COPY . /bot
CMD python main.py
必要なファイルを GitHub にプッシュする方法は、記事にまとめているので参考にしてみて下さい。



GitHub にリポジトリを用意できたら、Render Dashboard から [New Web Services] を選択します。
キャプチャ.PNG
この時点ではまだ、GitHub と連携できていないみたいでリポジトリが見つからないと思います（GitHub 連携でログインしたはずなんですが…）。右側から [Connect account] を選択し、GitHub と連携するか、Public Git repository から直接リポジトリの URL を指定しても構いません。
キャプチャ.PNG
GitHub と連携したら目的のリポジトリから [Connect] を選択して下さい（URL から直接指定する場合は、URL を入力後 [Continue] を選択して下さい）。そしたらプロジェクトの設定画面に移るので、適当に名前を入力し、[Region] として一番近いシンガポールを選択して下さい。[Runtime] は "Doker" のままで問題ありません。続いて環境変数の設定を行っていきます。スクロールしていくと、画面左下に [Advanced] があると思うので選択し、以下のように環境変数を設定して下さい。
キャプチャ.PNG
設定ができたら、[Create Web Service] を選択して下さい。自動的にデプロイが開始されます。私の環境では 80 秒程かかりました。デプロイが完了したら以下のように Web サーバの URL が表示されていると思います。この URL に Uptime Robot を用いて定期的にレスポンスを送ることにします。メモしておきましょう。

キャプチャ.PNG

Uptime Robot の設定
Uptime Robot とは無料で Web サイトの死活監視をモニタリングしてくれるサービスになります。サイトにアクセスし右上の [Register for FREE] からアカウントを作成して下さい。アカウントが作成できたら自動的に "Dashboard" ページに移動すると思います（移動しなかったらホームより [Go to Dashboard] を押して下さい）。次に左上の [Add New Monitor] から、監視対象を追加します。
キャプチャ.PNG
設定は、Monitor Type を HTTP(s)に、Friendly Name に適当な名前、URL に先程メモしておいた Render で表示された URL、Monitoring Interval を5分に設定（無料アカウントだと5分間隔が一番短い。アップグレードすると1分間隔に調整可能）、エラーが起きたときように Alert Contacts To Notify にチェックを入れ、右下の Create Monitor を押して完成です。
キャプチャ.PNG
これで Bot を動かしている Render に、5分間隔で ping を送れるようになりました。

ダウンタイムの検証
続いてダウンタイムの検証に移っていきます。検証期間は約3日間になります。検証に用いたファイル内容については以下記事を参考にして下さい。10秒以上応答しなかったらダウンタイムと見なしています。



ソースコードは以下になります。



結果として、ダウンした回数は7回あり、平均して18秒という結果になりました。そこそこ安定して稼働してくれているのではないでしょうか。

sample-01.png

ダウンタイム検証時の Discord チャンネルの様子は以下の通りです。回 "test" の削除がされていないことが分かります。これはちょうどダウンタイムと被ったためですね。2秒に1回 "test" メッセージを送っているので、ダウンタイムの時間からして、もっと多くあってもいいと思いますが、Render 上でラグがあって削除された、あるいは Raspberry Pi 上で "test" メッセージが送られなかったか、という推測ができます。Raspberry Pi 上で journalctl -u サービス名 と実行するとエラーが発生していることが確認できました。Raspberry Pi 上で "test" メッセージが送られなかった可能性の方が高そうです。

キャプチャ.PNG

最後に send.py と chk.py のサービスログを載せておきます。journalctl -u サービス名 でログの確認ができます。エラーが吐かれている箇所で確かに、ダウンタイムとして見なされていました。

サービスのログ
最後に
低性能の割に、比較的安定して稼働してくれているのではないでしょうか。ただ、Discord Bot を運用する上で第1候補になるかといわれると、それはないかなと思います。Railway が安定稼働してくれるので、そちらの方がいいと思います。