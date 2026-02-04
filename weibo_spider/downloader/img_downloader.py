from pathlib import Path

from .downloader import Downloader


class ImgDownloader(Downloader):
    def __init__(self, file_dir, file_download_timeout):
        super().__init__(file_dir, file_download_timeout)
        self.describe = '图片'
        self.key = ''

    async def handle_download(self, urls, w, session):
        """处理下载相关操作"""
        file_prefix = f"{w.publish_time[:10].replace('-', '')}_{w.id}"
        file_dir = self.file_dir / self.describe
        if not file_dir.is_dir():
            file_dir.mkdir(parents=True, exist_ok=True)
        media_key = self.key or 'original_pictures'
        if ',' in urls:
            url_list = urls.split(',')
            for i, url in enumerate(url_list):
                index = url.rfind('.')
                if len(url) - index >= 5:
                    file_suffix = '.jpg'
                else:
                    file_suffix = url[index:]
                file_name = f"{file_prefix}_{i + 1}{file_suffix}"
                file_path = file_dir / file_name
                ok = await self.download_one_file(url, file_path, w.id, session)
                if ok:
                    w.media.setdefault(media_key, []).append({
                        'url': url,
                        'path': file_path
                    })
        else:
            index = urls.rfind('.')
            if len(urls) - index > 5:
                file_suffix = '.jpg'
            else:
                file_suffix = urls[index:]
            file_name = f"{file_prefix}{file_suffix}"
            file_path = file_dir / file_name
            ok = await self.download_one_file(urls, file_path, w.id, session)
            if ok:
                w.media.setdefault(media_key, []).append({
                    'url': urls,
                    'path': file_path
                })
