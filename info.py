#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

# ---------------------------------------------------------------------------------
# Filmaffinity (ES) Tellico plugin
# Written by Fernando Damian Petrola
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation
# ---------------------------------------------------------------------------------

# Version 1.0.3: 2011-08-02
# * Update genres and plot fetching because of changes on filmaffinity page
# Version 1.0.2: 2011-08-01
# * Update images fetching because of changes on filmaffinity page
# Version 1.0.1: 2009-08-13
# * Bug fix for genre fields
# Version 1.0: 2009-08-12
# * Initial release.

import sys, os, re, md5, random
import urllib, urllib2, time, base64
import xml.dom.minidom
import string

XML_HEADER = """<?xml version="1.0" encoding="UTF-8"?>"""
DOCTYPE = """<!DOCTYPE tellico PUBLIC "-//Robby Stephenson/DTD Tellico V9.0//EN" "http://periapsis.org/tellico/dtd/v9/tellico.dtd">"""

VERSION = "0.4"

def trim(text,key1,key2):
	p1 = string.find(text,key1)
	if p1 == -1:
		return ""
	else:
		p1 = p1+len(key1)
	p2 = string.find(text[p1:],key2)
	if p2 == -1:
		return ""
	else:
		p2 = p1+p2
	return text[p1:p2]

def after(text,key):
	p1 = string.find(text,key)
	return text[p1+len(key):]

def genMD5():
	obj = md5.new()
	float = random.random()
	obj.update(str(float))
	return obj.hexdigest()

class BasicTellicoDOM:

	def __init__(self):
		self.__doc = xml.dom.minidom.Document()
		self.__root = self.__doc.createElement('tellico')
		self.__root.setAttribute('xmlns', 'http://periapsis.org/tellico/')
		self.__root.setAttribute('syntaxVersion', '9')
		
		self.__collection = self.__doc.createElement('collection')
		self.__collection.setAttribute('title', 'My Movies')
		self.__collection.setAttribute('type', '3')
		
		self.__fields = self.__doc.createElement('fields')
		# Add all default (standard) fields
		self.__dfltField = self.__doc.createElement('field')
		self.__dfltField.setAttribute('name', '_default')
		
		# Add a custom 'Collection' field
		self.__customField = self.__doc.createElement('field')
		self.__customField.setAttribute('name', 'titre-original')
		self.__customField.setAttribute('title', 'Original Title')
		self.__customField.setAttribute('flags', '8')
		self.__customField.setAttribute('category', 'General')
		self.__customField.setAttribute('format', '1')
		self.__customField.setAttribute('type', '1')
		self.__customField.setAttribute('i18n', 'yes')
		
		self.__fields.appendChild(self.__dfltField)
		self.__fields.appendChild(self.__customField)
		self.__collection.appendChild(self.__fields)

		self.__images = self.__doc.createElement('images')

		self.__root.appendChild(self.__collection)
		self.__doc.appendChild(self.__root)

		# Current movie id
		self.__currentId = 0


	def addEntry(self, movieData):
		"""
		Add a movie entry
		"""
		d = movieData
		entryNode = self.__doc.createElement('entry')
		entryNode.setAttribute('id', str(self.__currentId))

		titleNode = self.__doc.createElement('title')
		titleNode.appendChild(self.__doc.createTextNode(unicode(d['title'], 'latin-1').encode('utf-8')))

		otitleNode = self.__doc.createElement('titre-original')
		otitleNode.appendChild(self.__doc.createTextNode(unicode(d['otitle'], 'latin-1').encode('utf-8')))

		yearNode = self.__doc.createElement('year')
		yearNode.appendChild(self.__doc.createTextNode(unicode(d['year'], 'latin-1').encode('utf-8')))

		genresNode = self.__doc.createElement('genres')
		for g in d['genres']:
			genreNode = self.__doc.createElement('genre')
			genreNode.appendChild(self.__doc.createTextNode(unicode(g, 'latin-1').encode('utf-8')))
			genresNode.appendChild(genreNode)

		natsNode = self.__doc.createElement('nationalitys')
		natNode = self.__doc.createElement('nat')
		natNode.appendChild(self.__doc.createTextNode(unicode(d['nat'], 'latin-1').encode('utf-8')))
		natsNode.appendChild(natNode)

		castsNode = self.__doc.createElement('casts')
		for g in d['actors']:
			castNode = self.__doc.createElement('cast')
			col1Node = self.__doc.createElement('column')
			col2Node = self.__doc.createElement('column')
			col1Node.appendChild(self.__doc.createTextNode(unicode(g, 'latin-1').encode('utf-8')))
			castNode.appendChild(col1Node)
			castNode.appendChild(col2Node)
			castsNode.appendChild(castNode)

		dirsNode = self.__doc.createElement('directors')
		for g in d['dirs']:
			dirNode = self.__doc.createElement('director')
			dirNode.appendChild(self.__doc.createTextNode(unicode(g, 'latin-1').encode('utf-8')))
			dirsNode.appendChild(dirNode)

		timeNode = self.__doc.createElement('running-time')
		timeNode.appendChild(self.__doc.createTextNode(unicode(d['time'], 'latin-1').encode('utf-8')))

		filmaffinityNode = self.__doc.createElement(unicode('filmaffinity-link', 'latin-1').encode('utf-8'))
		filmaffinityNode.appendChild(self.__doc.createTextNode(unicode(d['filmaffinity'], 'latin-1').encode('utf-8')))

		plotNode = self.__doc.createElement('plot')
		plotNode.appendChild(self.__doc.createTextNode(unicode(d['plot'], 'latin-1').encode('utf-8')))

		if d['image']:
			imageNode = self.__doc.createElement('image')
			imageNode.setAttribute('format', 'JPEG')
			imageNode.setAttribute('id', d['image'][0])
			imageNode.setAttribute('width', '120')
			imageNode.setAttribute('height', '160')
			imageNode.appendChild(self.__doc.createTextNode(unicode(d['image'][1], 'latin-1').encode('utf-8')))

			coverNode = self.__doc.createElement('cover')
			coverNode.appendChild(self.__doc.createTextNode(d['image'][0]))

		writerNode = self.__doc.createElement('writer')
		writerNode.appendChild(self.__doc.createTextNode(unicode(d['writer'], 'latin-1').encode('utf-8')))

		composerNode = self.__doc.createElement('composer')
		composerNode.appendChild(self.__doc.createTextNode(unicode(d['composer'], 'latin-1').encode('utf-8')))

		producerNode = self.__doc.createElement('producer')
		producerNode.appendChild(self.__doc.createTextNode(unicode(d['producer'], 'latin-1').encode('utf-8')))

		photosNode = self.__doc.createElement('photos')
		photosNode.appendChild(self.__doc.createTextNode(unicode(d['photos'], 'latin-1').encode('utf-8')))

		for name in (	'titleNode', 'otitleNode', 'yearNode', 'genresNode', 'natsNode', 
						'castsNode', 'dirsNode', 'timeNode', 'filmaffinityNode', 'plotNode', 'writerNode', 'composerNode', 'producerNode', 'photosNode' ):
			entryNode.appendChild(eval(name))

		if d['image']:
			entryNode.appendChild(coverNode)
			self.__images.appendChild(imageNode)

		self.__collection.appendChild(entryNode)
		
		self.__currentId += 1

	def printXML(self):
		self.__collection.appendChild(self.__images)
		print XML_HEADER; print DOCTYPE
		print self.__root.toxml()


class FilmaffinityParser:
	def __init__(self):
		self.__searchURL= 'http://www.filmaffinity.com/es/advsearch.php?stext=%s'
		self.__movieURL = 'http://www.filmaffinity.com/es/film'

		# Define some regexps
		self.__regExps = { 	'title' 	: '<img src="http://www.filmaffinity.com/images/movie.gif" border="0">(?P<title>.+?)</span>',
						'dirs'		: '(?P<step1><b>DIRECTOR</b>?)', 
						'actors' 	: '(?P<step1><b>REPARTO</b>)',
						'image'	: '<img src="(?P<image>http://pics.filmaffinity.com/[^"]+full.jpg)"'}

		self.__domTree = BasicTellicoDOM()

	def run(self, title):
		self.__getMovie(title)
		self.__domTree.printXML()

	def __getHTMLContent(self, url):
		u = urllib2.urlopen(url)
		self.__data = u.read()
		u.close()

	def __fetchMovieLinks(self):
		matchList = re.findall("""<b><a *href="/es/film(?P<page>.*?\.html?)">(?P<title>.*?)</a>""", self.__data)
		if not matchList: return None

		return matchList

	def __fetchMovieInfo(self, url):
		self.__getHTMLContent(url)

		matches = data = {}
		
		for name, regexp in self.__regExps.iteritems():
			if name == 'image':
				matches[name] = re.findall(self.__regExps[name], self.__data, re.S | re.I)
			else:
				matches[name] = re.search(regexp, self.__data)

			if matches[name]:
				if name == 'title':
					data[name] = matches[name].group('title').strip()
				elif name == 'dirs':
					self.director = trim(self.__data,'<b>DIRECTOR</b></td>', '</a>')
					self.director = after(self.director, '">')
					data[name] = []
					data[name].append(self.director)

				elif name == 'actors':
					actorsList = re.sub('</?a.*?>', '', trim(self.__data, '<b>REPARTO</b></td>', '</td>')).split(',')
					data[name] = []

					for d in actorsList:
						data[name].append(string.replace(d.strip(), '<td  >', ''))

				elif name == 'image':
					md5 = genMD5()

					imObj = urllib2.urlopen(matches[name][0].strip())
					img = imObj.read()
					imObj.close()
					imgPath = "/tmp/%s.jpeg" % md5
					try:
						f = open(imgPath, 'w')
						f.write(img)
						f.close()
					except:
						pass

					data[name] = (md5 + '.jpeg', base64.encodestring(img))
					try:
						os.remove(imgPath)
					except:
						pass
			else:
				matches[name] = ''

		data['year'] = trim(self.__data, '<b>AÑO</b></td>', '</td>')
		data['year'] = after(data['year'], '<td >')

		data['nat'] = trim(self.__data, '<b>PAÍS</b></td>', '</td>')
		data['nat'] = trim(data['nat'], 'title="', '"')

		self.time = trim(self.__data, '<b>DURACIÓN</b></td>', '</td>')
		self.time = after(self.time, '<td>')
		data['time'] = trim(self.time, '<td>', ' min.')

		self.genre = trim(self.__data, '<b>GÉNERO</b>', '</tr>')
		if self.genre == '':
			self.genre = trim(self.__data, '<b>G&Eacute;NERO</b>', '</tr>')

		self.genre= re.compile('<a[^>]+>').sub('', self.genre)
		self.genre= self.genre.replace('</a>', '')
		self.genre= self.genre.replace('</td>', '')
		self.genre = self.genre.replace('<td valign="top">', '')
		self.genre= re.compile('\s\s').sub('', self.genre)
		self.genre= self.genre.replace('.', '|')
		

#		self.genre= self.genre.split('/')

#		if len(self.genre) > 2:
#			self.genre= self.genre[1]
#		else:
#			self.genre= self.genre[0]

		self.genre = self.genre.split('|')

		data['genres']= []
		for d in self.genre:
			data['genres'].append(d.strip())

		self.o_title = trim(self.__data, '<b>TITULO ORIGINAL</b></td>', '</b></td>')
		self.o_title = after(self.o_title, '<b>')
		data['otitle']= self.o_title

		self.plot = trim(self.__data, '<b>SINOPSIS</b>', '</tr>')
		self.plot = after(self.plot, '<td>')
		self.plot= self.plot.replace('</td>', '');
		self.plot = string.replace(self.plot, '(FILMAFFINITY)', '')
		self.o_title = trim(self.__data, 'SINOPSIS:', '(FILMAFFINITY)')
		if len(self.o_title) == 0:
			data['plot']= self.plot
		else:
			data['plot']= self.o_title

		if self.update:
			data['title']= self.title;

		self.writer = after(trim(self.__data, '<b>GUIÓN</b></td>', '</td>'), '<td >')
		data['writer'] = self.writer

		self.composer = after(trim(self.__data, '<b>MÚSICA</b></td>', '</td>'), '<td  >')
		data['composer'] = self.composer

		self.photos = after(trim(self.__data, '<b>FOTOGRAFÍA</b></td>', '</td>'), '<td  >')
		data['photos'] = self.photos

		self.producer = after(trim(self.__data, '<b>PRODUCTORA</b></td>', '</td>'), '<td  >')
		data['producer'] = self.producer

		return data

	def getLinks (self, title, pageNumber):
		if not len(title): return

		self.__title = title
		self.__getHTMLContent(self.__searchURL % urllib.quote(self.__title)+ "&page="+str(pageNumber))
		links = self.__fetchMovieLinks()
		return links

	def __getMovie(self, title):
		pageNumber= 1;
		links= self.getLinks(title, pageNumber);
		while links:
			for entry in links:
				data = self.__fetchMovieInfo( url = "%s%s" % (self.__movieURL, entry[0]) )
				data['filmaffinity'] = "%s%s" % (self.__movieURL, entry[0])
				self.__domTree.addEntry(data)

			pageNumber+= 1
			links= self.getLinks(title, pageNumber)

		
		return None



def showUsage():
	print "Usage: %s movietitle" % sys.argv[0]
	print "for updates use: %s movietitle -u" % sys.argv[0]
	sys.exit(1)

def main():
	if len(sys.argv) < 2:
		showUsage()

	parser = FilmaffinityParser()
	parser.title= sys.argv[1];
	parser.update= len(sys.argv) > 2;
	parser.run(sys.argv[1])

if __name__ == '__main__':
	main()
