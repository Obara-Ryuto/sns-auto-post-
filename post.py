import os
import random
import requests
from pathlib import Path
from google import genai

# 環境変数から設定を読み込む
INSTAGRAM_ACCESS_TOKEN = os.environ['INSTAGRAM_ACCESS_TOKEN']
INSTAGRAM_USER_ID = os.environ['INSTAGRAM_USER_ID']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

GITHUB_REPO = 'Obara-Ryuto/sns-auto-post-'
GITHUB_BRANCH = 'main'


def get_random_image():
    images_dir = Path('images')
    image_files = (
        list(images_dir.glob('*.jpg')) +
        list(images_dir.glob('*.jpeg')) +
        list(images_dir.glob('*.png'))
    )
    if not image_files:
        raise Exception('images/ フォルダに画像がありません')
    return random.choice(image_files)


def get_image_url(image_path):
    filename = image_path.name
    return f'https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/images/{filename}'


def generate_caption():
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = """
あなたはWEB商店街のInstagram投稿担当です。
以下の事業内容を参考に、Instagramの投稿キャプションを日本語で生成してください。

【事業内容】
WEB商店街とは、WEB上の街を歩きながら地域のお店と出会えるサービスです。
- お店の写真からAIがミニチュア建物を自動生成
- クォータービュー（斜め上から見下ろす視点）で街を表現
- 街に動き（人、鳥、木の葉など）を加えて生命感を演出
- ランドマーク（広場、神社、時計塔など）で目的地を作る
- スタンプラリーで複数のお店を巡る楽しさを提供
- 開発者：小原 隆人

【投稿テーマ】（以下から1つをランダムに選んで書いてください）
1. WEB商店街のコンセプト・世界観の紹介
2. AIによるお店のミニチュア建物生成技術の紹介
3. 地域のお店オーナーへの参加呼びかけ
4. ユーザーへのWEB散歩体験の紹介
5. スタンプラリー機能の楽しさ紹介
6. 街づくりへの想いや背景

【条件】
- 150〜200文字程度
- 親しみやすくカジュアルなトーン
- 最後に関連するハッシュタグを5〜8個つける
- ハッシュタグ例：#WEB商店街 #地域活性化 #まちづくり #商店街 #バーチャル #AI #地域のお店 #街づくり

キャプションのみを出力してください。
"""

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt
    )
    return response.text.strip()


def post_to_instagram(image_url, caption):
    import time

    # Step 1: メディアコンテナを作成
    container_response = requests.post(
        f'https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media',
        data={
            'image_url': image_url,
            'caption': caption,
            'access_token': INSTAGRAM_ACCESS_TOKEN
        }
    )
    if not container_response.ok:
        print(f'Instagram エラー詳細: {container_response.text}')
        container_response.raise_for_status()
    container_id = container_response.json()['id']
    print(f'コンテナ作成完了: {container_id}')

    # Step 2: コンテナの処理完了を待つ
    for i in range(10):
        time.sleep(5)
        status_response = requests.get(
            f'https://graph.instagram.com/v21.0/{container_id}',
            params={
                'fields': 'status_code',
                'access_token': INSTAGRAM_ACCESS_TOKEN
            }
        )
        status = status_response.json().get('status_code')
        print(f'コンテナ状態: {status}')
        if status == 'FINISHED':
            break
        if status == 'ERROR':
            raise Exception(f'コンテナ処理エラー: {status_response.text}')

    # Step 3: 投稿を公開
    publish_response = requests.post(
        f'https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media_publish',
        data={
            'creation_id': container_id,
            'access_token': INSTAGRAM_ACCESS_TOKEN
        }
    )
    if not publish_response.ok:
        print(f'公開エラー詳細: {publish_response.text}')
        publish_response.raise_for_status()
    return publish_response.json()


def main():
    print('Instagram自動投稿を開始します...')

    image_path = get_random_image()
    print(f'選択した画像: {image_path}')

    image_url = get_image_url(image_path)
    print(f'画像URL: {image_url}')

    print('キャプションを生成中...')
    caption = generate_caption()
    print(f'キャプション:\n{caption}')

    print('Instagramに投稿中...')
    result = post_to_instagram(image_url, caption)
    print(f'投稿完了！ ID: {result}')


if __name__ == '__main__':
    main()
