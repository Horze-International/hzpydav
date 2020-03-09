import requests
from bs4 import BeautifulSoup

class Client:
	def __init__(self, base_url, auth, cert, cafile=None):
		self.base_url = base_url

		self.session = requests.Session()
		self.session.auth = auth
		self.session.cert = cert

		if cafile != None:
			self.session.verify = cafile

	def exists(self, url):
		response = self.session.request('PROPFIND', self.base_url + url)

		code = response.status_code

		if code == 404:
			return False
		else:
			return True

	def propfind(self, url):
		return_value = {}

		response = self.session.request('PROPFIND', self.base_url + url)

		code = response.status_code

		if code == 404:
			print('Could not find ' + url)
			return return_value
		elif code != 200 and code != 207:
			print('Propfind failed for ' + url + ': unknown error (' + str(code) + ')')
			return return_value

		soup = BeautifulSoup(response.text, 'lxml')

		return_value['is_dir'] = False
		return_value['entries'] = []
		
		metadata = soup.find('response')

		if metadata.find('propstat').find('prop').find('resourcetype').find('collection') != None:
			return_value['is_dir'] = True

		first = True

		for file in soup.find_all('response'):
			# First entry is the file itself, subsequent entries are directory entries
			if first:
				first = False
				continue

			return_value['entries'].append(file.find('href').text)

		return return_value

	def mkdir(self, url, recursive=False):
		if url[-1] == '/':
			url = url[:-1]

		# Since this is the base case for recursion, don't print any errors
		if self.exists(url):
			return

		parent = '/'.join(url.split('/')[:-1])

		if not self.exists(parent):
			if recursive == False:
				print('Could not create directory ' + url + ', parent does not exist')
				return
			else:
				self.mkdir(parent, True)

		response = self.session.request('MKCOL', self.base_url + url)

		code = response.status_code

		if code == 201:
			return
		elif code == 405:
			print('Could not create ' + url + ': already exists')
		else:
			print('Could not create ' + url + ': unknown error (' + str(code) + ')')

	def upload(self, url, file):
		data = file.read()

		parent = '/'.join(url.split('/')[:-1])

		self.mkdir(parent, True)

		print('Uploading: ' + url)

		self.session.put(self.base_url + url, data=data, headers={'Content-Type': 'application/octet-stream'})

	# Traverse folder recursively, returning a list of absolute filenames
	def traverse(self, folder):
		entries = self.propfind(folder)['entries']

		results = []

		for entry in entries:
			# if folder, recurse
			if entry[-1] == '/':
				results = results + self.traverse(entry)
			else:
				results.append(entry)

		return results
