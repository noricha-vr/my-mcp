#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VRChat技術・学術系イベントのウェブページからイベント情報を抽出するスクリプト
集会名、日付、日時、発表者、テーマを抽出してCSVファイルに保存する
"""

import asyncio
import csv
from datetime import datetime
from playwright.async_api import async_playwright

# 対象URL
TARGET_URL = "https://vrc-ta-hub.com/event/detail/history/"

async def extract_event_data():
    """
    PlaywrightでWebページにアクセスしてテーブルデータを抽出する
    """
    async with async_playwright() as p:
        # ブラウザを起動
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # ターゲットURLにアクセス
        print(f"ページにアクセス中: {TARGET_URL}")
        await page.goto(TARGET_URL)
        
        # ページの読み込みを待機
        await page.wait_for_load_state("networkidle")
        
        # 全ページのデータを取得するためのリスト
        all_events_data = []
        
        # 最初のページの処理
        current_page = 1
        has_next_page = True
        
        while has_next_page:
            print(f"ページ {current_page} の処理中...")
            
            # テーブルから行を取得
            rows = await page.query_selector_all("table tr:not(:first-child)")
            
            if not rows:
                print("テーブルの行が見つかりません。セレクタを確認してください。")
                # ページのHTMLをログに出力（デバッグ用）
                html = await page.content()
                print(f"ページHTML（先頭100文字）: {html[:100]}...")
                break
            
            print(f"{len(rows)}行のデータを抽出します")
            
            # 各行のデータを抽出
            for row in rows:
                # 各セルからテキストを抽出
                cells = await row.query_selector_all("td")
                if len(cells) < 6:
                    print(f"警告: 行のセル数が不足しています ({len(cells)} < 6)")
                    continue
                
                try:
                    # テキストデータを取得
                    community_name = await cells[0].inner_text()
                    community_name = community_name.strip()
                    
                    date = await cells[1].inner_text()
                    date = date.strip()
                    
                    time = await cells[2].inner_text()
                    time = time.strip()
                    
                    # 資料セルはスキップ
                    
                    speaker = await cells[4].inner_text()
                    speaker = speaker.strip()
                    
                    theme = await cells[5].inner_text()
                    theme = theme.strip()
                    
                    # リンクからイベント詳細URLを取得
                    theme_link = await cells[5].query_selector("a")
                    event_url = ""
                    if theme_link:
                        event_url = await theme_link.get_attribute("href")
                        if event_url:
                            event_url = f"https://vrc-ta-hub.com{event_url}"
                    
                    # データを格納
                    event = {
                        "集会名": community_name,
                        "日付": date,
                        "時間": time,
                        "発表者": speaker,
                        "テーマ": theme,
                        "イベントURL": event_url
                    }
                    
                    all_events_data.append(event)
                    
                except Exception as e:
                    print(f"行の処理中にエラーが発生しました: {e}")
            
            # 次のページがあるか確認
            next_page_link = await page.query_selector(f"a:text-is(\"{current_page + 1}\")")
            
            if next_page_link:
                print(f"次のページ {current_page + 1} に移動します")
                await next_page_link.click()
                await page.wait_for_load_state("networkidle")
                current_page += 1
            else:
                has_next_page = False
                print("次のページはありません。抽出を終了します。")
        
        # ブラウザを閉じる
        await browser.close()
        
        print(f"合計 {len(all_events_data)} 件のイベントデータを抽出しました")
        return all_events_data

def save_to_csv(data, output_file=None):
    """
    抽出したデータをCSVファイルに保存する
    """
    if not data:
        print("データが見つかりませんでした")
        return
    
    # 出力ファイル名が指定されていない場合、現在時刻を含めたファイル名を生成
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"vrc_events_{timestamp}.csv"
    
    # CSVのフィールド名
    fieldnames = ["集会名", "日付", "時間", "発表者", "テーマ", "イベントURL"]
    
    # CSVファイルに書き込み（BOMありUTF-8で出力）
    with open(output_file, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"{len(data)}件のイベントデータを {output_file} に保存しました")
    return output_file

def save_to_tsv(data, output_file=None):
    """
    抽出したデータをTSVファイルに保存する（CSVで問題がある場合の代替手段）
    """
    if not data:
        print("データが見つかりませんでした")
        return
    
    # 出力ファイル名が指定されていない場合、現在時刻を含めたファイル名を生成
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"vrc_events_{timestamp}.tsv"
    
    # TSVのフィールド名
    fieldnames = ["集会名", "日付", "時間", "発表者", "テーマ", "イベントURL"]
    
    # TSVファイルに書き込み
    with open(output_file, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(data)
    
    print(f"{len(data)}件のイベントデータを {output_file} に保存しました")
    return output_file

async def main():
    """
    メイン関数
    """
    print("VRChat技術・学術系イベント情報の抽出を開始します...")
    
    try:
        # イベントデータを抽出
        events_data = await extract_event_data()
        
        # CSVファイルに保存
        csv_file = save_to_csv(events_data)
        
        # TSVファイルにも保存（バックアップとして）
        tsv_file = save_to_tsv(events_data)
        
        print(f"処理が完了しました。データは以下のファイルに保存されています：")
        print(f"- CSV形式: {csv_file}")
        print(f"- TSV形式: {tsv_file}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
