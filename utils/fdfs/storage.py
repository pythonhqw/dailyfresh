from django.core.files.storage import FileSystemStorage
from fdfs_client.client import Fdfs_client


class FdfsStorage(FileSystemStorage):
    """自定义存储类：当管理员在后台上传文件时，会使用此类保存上传的文件"""

    def _save(self, name, content):

        # path = super()._save(name, content)
        # todo:保存文件到FastDfs服务器上
        client = Fdfs_client('utils/fdfs/client.conf')
        try:
            # 上传文件到Fdfs服务器上
            datas = content.read()
            result = client.upload_by_buffer(datas)

            status = result.get('Status')
            if status == 'Upload successed.':
                # 上传图片成功
                path = result.get('Remote file_id')
            else:
                raise Exception('上传图片失败')
        except Exception as e:
            raise e

        return path

    def url(self, name):
        # 拼接nginx服务器的ｉｐ和端口，再返回给浏览器显示
        path = super().url(name)
        return 'http://127.0.0.1:8888/' + path






