from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.jobs import CondorJobTemplate


class SswDownloader(TethysAppBase):
    """
    Tethys app class for SSW Downloader.
    """

    name = 'SSW Downloader'
    index = 'ssw_downloader:home'
    icon = 'ssw_downloader/images/nasa_icon.png'
    package = 'ssw_downloader'
    root_url = 'ssw-downloader'
    color = '#141321'
        
    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (UrlMap(name='home',
                           url='ssw-downloader',
                           controller='ssw_downloader.controllers.home'),
                    UrlMap(name='jobs',
                           url='ssw-downloader/jobs',
                           controller='ssw_downloader.controllers.jobs'),
                    UrlMap(name='results',
                           url='ssw-downloader/{job_id}/results',
                           controller='ssw_downloader.controllers.results'),
                    UrlMap(name='download',
                           url='ssw-downloader/{job_id}/download',
                           controller='ssw_downloader.controllers.download'),
                    UrlMap(name='convert',
                           url='ssw-downloader/{job_id}/convert',
                           controller='ssw_downloader.controllers.convert')
        )

        return url_maps

    def job_templates(self):
        """
        Define job templates
        """

        job_templates = (CondorJobTemplate(name='ssw_download',
                                       parameters={'executable': '$(APP_WORKSPACE)/download_nldas_data.py',
                                                   'condorpy_template_name': 'vanilla_transfer_files',
                                                   'attributes': {'transfer_output_files': ('$(job_name).nc',),},
                                                   'scheduler': None,
                                                   'remote_input_files': ('$(APP_WORKSPACE)/download_nldas_data.py',),
                                                  }
                                      ),
                    )

        return job_templates