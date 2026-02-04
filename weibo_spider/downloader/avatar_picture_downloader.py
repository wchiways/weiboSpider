from pathlib import Path

from .img_downloader import ImgDownloader


class AvatarPictureDownloader(ImgDownloader):
    def __init__(self, file_dir, file_download_timeout):
        super().__init__(file_dir, file_download_timeout)
        self.describe = '头像图片'
        self.key = 'avatar_pictures'

    async def handle_download(self, urls, session):
        """处理下载相关操作"""
        file_dir = self.file_dir / self.describe
        if not file_dir.is_dir():
            file_dir.mkdir(parents=True, exist_ok=True)

        for i, url in enumerate(urls):
            index = url.rfind('/')
            file_name = url[index:]
            file_path = file_dir / file_name
            await self.download_one_file(url, file_path, 'xxx', session)