from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.core.servers.basehttp import FileWrapper

from tethys_gizmos.gizmo_options import TextInput, JobsTable

from app import SswDownloader as app
import os
import time
import urllib
import urllib2

@login_required
def home(request):
    """
    Controller for the app home page.
    """

    text_input_options = TextInput(name='urls_url',
                                   icon_append='glyphicon glyphicon-link',

                                   )

    if request.POST and 'urls_url' in request.POST:
        urls_url = request.POST['urls_url']

        # configure and submit condor job
        jm = app.get_job_manager()
        job_name = 'SSW Download-%s' % time.time()
        job_description = _get_description(urls_url)
        job = jm.create_job(job_name, request.user, 'ssw_download', description=job_description)
        job.set_attribute('arguments', '"%s $(job_name).nc"' % (urls_url, ))
        # job.set_attribute('arguments', [urls_url, '%s.nc' % job.name])
        job.execute()

        # redirect to jobs page
        return redirect('jobs/')

    context = {'text_input_options': text_input_options}

    return render(request, 'ssw_downloader/home.html', context)


def _get_description(urls_url):

    def get_url_variables(url):
        raw_pairs = url.split('?')[1].split('&')
        url_vars = dict()
        for pair in raw_pairs:
            k,v = pair.split('=')
            url_vars[k] = v
        return url_vars

    def get_date(url_vars):
        date = url_vars['LABEL'].split('.')[1]
        date_str = "%s-%s-%s" % (date[1:5], date[5:7], date[7:9])
        return date_str

    urls = urllib2.urlopen(urls_url).read().strip().split()
    first_url = urllib.unquote(urls[0])
    last_url = urllib.unquote(urls[-1])
    url_vars = get_url_variables(first_url)
    bbox = url_vars['BBOX']
    from_date = get_date(url_vars)
    to_date = get_date(get_url_variables(last_url))
    num_files = len(urls)

    description = "FILES: %d; DATES: %s to %s; BBOX: %s" % (num_files, from_date, to_date, bbox)
    return description



@login_required
def jobs(request):
    """
    Controller for the jobs page.
    """

    jm = app.get_job_manager()

    jobs = jm.list_jobs(request.user)

    jobs_table_options = JobsTable(jobs=jobs,
                                   column_fields=('id', 'description', 'run_time'),
                                   hover=True,
                                   striped=False,
                                   bordered=False,
                                   condensed=False,
                                   results_url='ssw_downloader:results',
                                   )

    context = {'jobs_table_options': jobs_table_options}

    return render(request, 'ssw_downloader/jobs.html', context)


@login_required
def results(request, job_id):
    """
    Controller for the results page.
    """

    context = {'job_id': job_id}

    return render(request, 'ssw_downloader/results.html', context)

@login_required
def download(request, job_id):
    jm = app.get_job_manager()
    job = jm.get_job(job_id)

    file_name = '%s.nc' % job.condorpy_job.job_name
    file_path = os.path.join(job.initial_dir, file_name)

    wrapper = FileWrapper(file(file_path))
    response = HttpResponse(wrapper, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)
    response['Content-Length'] = os.path.getsize(file_path)
    return response