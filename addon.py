import re
import os
import sys
import urllib
import urlparse
import requests
import xbmcgui
import xbmcplugin

URL  = 'https://infocon.org/'
DEBUG = True
NAME = 'Infocon'
#TODO; add more video files
SUPPORTED_VIDEO_FILES = ['.mp4','.avi']

# plugin://plugin.video.infocon
base_url = sys.argv[0]
# process handle (numeric)
addon_handle = int(sys.argv[1])
# from from query to dict parameters
args = urlparse.parse_qs(sys.argv[2][1:])
# files, songs, artists, albums, movies, tvshows, episodes, musicvideos
xbmcplugin.setContent(addon_handle, 'episodes')
#  get the value of "mode" parameter
mode = args.get('mode', None)


def build_url(query):
	return base_url + '?' + urllib.urlencode(query)


def log(s, debug_only=False, error=False):
    if DEBUG or not debug_only:
        xbmc.log('[%s] %s' % (NAME,s))
    if error:
        raise_error(s)


def get_list(url):
    r = requests.get(url)
    if r.status_code != 200:
        log('Received staus %d calling url % s' % (r.status_code,url), error=True)
    else:
        table = r.text.split('<tbody>')[1].split('</tbody>')[0]
        lines = table.split('\n')

        links = []
        names = []

        for line in lines:
            links.append(re.findall('<a href="([^>]+)" title=".*?">.*?</a>',line))
            names.append(re.findall('<a href="[^>]+" title=".*?">(.*?)</a>',line))
            links = [''.join(l) for l in links]
            names = [n for n in names]

        if len(links) != len(names):
            log('Links retrieved from page %s are not as many as corresponding names' % url, error=True)
            return [[],[]]

        return [links,names]


def build_menu(current_url,links,names):

	for link in links:

		file, ext = os.path.splitext(link)
		entry_name = urllib.unquote(file)
		itemURL = current_url + link
		log(' ------------- ', debug_only=True)

		# if it's a video file to be played
		if ext.lower() in SUPPORTED_VIDEO_FILES:
			# TODO: evaluate whether to do a head request to confirm mime type
			log('creating a file list for %s' % itemURL, debug_only=True)
			li = xbmcgui.ListItem(entry_name)
			li.setProperty('isPlayable' , 'true')
			url = build_url({'mode': 'play_video', 'filename': entry_name, 'itemURL' : itemURL})
			log(url, debug_only=True)
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)

		# else if it's a directory to be listed
		elif not ext and file.endswith('/'):
			log('creating a folder list for %s' % itemURL, debug_only=True)
			li = xbmcgui.ListItem(entry_name)
			url = build_url({'mode': 'folder', 'foldername': entry_name, 'current_url' : itemURL })
			log(url, debug_only=True)
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
		else:
			log('nothing to do for %s' % entry_name, debug_only=True)
			log('with extension %s \t url: %s' % (ext, itemURL), debug_only=True)

	xbmcplugin.endOfDirectory(addon_handle)

# TODO: add date
def play_video(itemURL, title, date=''):

	log('about to play %s' % itemURL, debug_only=True)
	play_item = xbmcgui.ListItem(path=itemURL)
	play_item.setInfo('video', {'title': title})

	# set subtitles 
	_, ext = os.path.splitext(itemURL)
	subs_url = itemURL.replace(ext,'.srt')#
	r = requests.head(subs_url)
	if r.status_code == 200:
		log('Setting subtitles file %s' % subs_url)
		play_item.setSubtitles([subs_url])
	xbmc.Player().play(itemURL, play_item)





try:
	if mode is None:
		log('Inside main function, mode = None', debug_only=True)
		url = build_url({'mode': 'folder', 'foldername': '/', 'current_url' : URL })
		log(url, debug_only=True)
		li = xbmcgui.ListItem('/')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
		listitem=li, isFolder=True)
		#url = build_url({'mode': 'folder', 'foldername': 'Folder Two'})
		#li = xbmcgui.ListItem('Folder Two', iconImage='DefaultFolder.png')
		#xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
		#listitem=li, isFolder=True)
		xbmcplugin.endOfDirectory(addon_handle)

	# if we are listing a directory content
	elif mode[0] == 'folder':
		log('Inside folder mode', debug_only=True)
		foldername = args['foldername'][0]
		current_url = args['current_url'][0]
		log('inside folder ' + foldername + ' with url ' + current_url, debug_only=True)
		[links,names] = get_list(current_url)
		log('received %d links' % len(links), debug_only=True)
		build_menu(current_url,links,names)

	elif mode[0] == 'play_video':
		log('Inside play_video mode', debug_only=True)
		filename = args['filename'][0] 
		itemURL = args['itemURL'][0]
		# subURL
		play_video(itemURL,filename)


except Exception as ex:
	log(str(ex))


