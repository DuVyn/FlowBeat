"""
FlowBeat 批量上传脚本 (Dev Tool)
需要安装依赖: pip install httpx
"""
import os
import httpx
import asyncio
from pathlib import Path

# --- 配置 ---
API_BASE = "http://localhost:8000/api/v1"
MUSIC_DIR = r"D:\Download\音乐"  # 你的本地音乐目录
# 登录账号 (必须是管理员)
USERNAME = "admin@example.com"
PASSWORD = "stringst"


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 登录获取 Token
        print(f"正在登录 {USERNAME}...")
        resp = await client.post(f"{API_BASE}/auth/login/access-token", data={
            "username": USERNAME,
            "password": PASSWORD
        })
        if resp.status_code != 200:
            print(f"登录失败: {resp.text}")
            return

        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("登录成功！")

        # 2. 遍历文件
        folder = Path(MUSIC_DIR)
        for file_path in folder.glob("*.flac"):
            print(f"\n正在处理: {file_path.name}")

            # 解析文件名: "Unstoppable_-_Sia.flac" -> Title: Unstoppable, Artist: Sia
            # 注意：这取决于你的文件名格式，此处根据截图假设为 Title_-_Artist.ext
            try:
                stem = file_path.stem  # 去掉后缀
                if "_-_" in stem:
                    parts = stem.split("_-_")
                    title_str = parts[0].strip()
                    artist_name = parts[1].strip()
                else:
                    title_str = stem
                    artist_name = "未知艺术家"
            except Exception:
                title_str = file_path.stem
                artist_name = "未知艺术家"

            # 3. 检查或创建艺术家
            # 简化逻辑：这里不做去重查询，直接尝试创建，如果已存在（唯一索引冲突）则需要查询ID
            # 为演示简单，假设每次都查一下列表
            artists_resp = await client.get(f"{API_BASE}/music/artists", headers=headers)
            artists = artists_resp.json()
            artist_id = next((a["id"] for a in artists if a["name"] == artist_name), None)

            if not artist_id:
                print(f"  -> 创建艺术家: {artist_name}")
                new_art = await client.post(f"{API_BASE}/music/artists", json={"name": artist_name}, headers=headers)
                if new_art.status_code != 200:
                    print(f"  [Error] 创建艺术家失败: {new_art.text}")
                    continue
                artist_id = new_art.json()["id"]
            else:
                print(f"  -> 艺术家已存在: {artist_name} (ID: {artist_id})")

            # 4. 检查或创建专辑 (默认创建一个同名专辑或通用专辑)
            album_title = f"{artist_name}的热门单曲"
            # 同样简化逻辑，获取该艺术家的专辑
            albums_resp = await client.get(f"{API_BASE}/music/artists/{artist_id}/albums", headers=headers)
            albums = albums_resp.json()
            album_id = next((a["id"] for a in albums if a["title"] == album_title), None)

            if not album_id:
                print(f"  -> 创建专辑: {album_title}")
                # 默认发行日期设为 2020-01-01
                new_alb = await client.post(f"{API_BASE}/music/albums", json={
                    "title": album_title,
                    "release_date": "2020-01-01",
                    "artist_id": artist_id
                }, headers=headers)
                if new_alb.status_code != 200:
                    print(f"  [Error] 创建专辑失败: {new_alb.text}")
                    continue
                album_id = new_alb.json()["id"]
            else:
                print(f"  -> 专辑已存在 (ID: {album_id})")

            # 5. 上传文件
            print(f"  -> 开始上传文件...")
            files = {'file': (file_path.name, open(file_path, 'rb'), 'audio/flac')}
            data = {
                "title": title_str,
                "duration": 200,  # 这里的时长暂时硬编码，实际应使用 mutagen 库读取 FLAC 时长
                "album_id": album_id,
                "track_number": 1
            }

            upload_resp = await client.post(f"{API_BASE}/music/upload", data=data, files=files, headers=headers)

            if upload_resp.status_code == 200:
                print(f"  [Success] 上传成功! ID: {upload_resp.json()['id']}")
            else:
                print(f"  [Fail] 上传失败: {upload_resp.text}")

            # 关闭文件句柄
            files['file'][1].close()


if __name__ == "__main__":
    asyncio.run(main())
