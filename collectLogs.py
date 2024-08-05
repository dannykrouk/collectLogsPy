# run this script as local machine admin
# "E:\Program Files\ArcGIS\Server\framework\runtime\ArcGIS\bin\Python\Scripts\propy.bat" "collectLogs.py"
import sys 
import os
import json
from os import environ
import time
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import configparser
from pathlib import Path
import argparse
import ctypes
import socket

def main(argv=None):
	
	print('### COLLECTION PROCESS BEGINNING ###')
	
	# globals
	global bOsLogsCollected
	global bWebServerLogsCollected
	global bWebAdaptorLogsCollected
	global outputDir
	bOsLogsCollected = False
	bWebServerLogsCollected = False
	bWebAdaptorLogsCollected = False 
	outputDir = setupOutputDir()

	# The user can specify their own config file.
	# If they don't we use the default.
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', '--file')
	args = parser.parse_args()
	configFile = args.file
	if configFile is None:
		configFile = 'config.ini'
		print ('Using default configuration file')
	else:
		print('Using supplied config file: ' + configFile)
	
	create_config()
	config_values = read_config(configFile)
	print('Configuration file read')

	# are we running as local admin?
	is_admin = runningAsAdmin()
	if is_admin == False:
		print('Pre-condition failure.  Exiting.  Please run this script as a local admin')
		sys.exit()
	else:
		print('Confirmed admin privileges')

	# get the environment variables
	agsPath = environ.get('AGSSERVER')
	prtlPath = environ.get('AGSPORTAL')
	dsPath = environ.get('AGSDATASTORE')
	
	# set the paths if the env variable are not present
	if agsPath is None:
		print('AGSSERVER environment variable not present. Using configuration file value instead.')
		agsPath = config_values['esriAgsPath']
	if prtlPath is None:
		prtlPath = config_values['esriPrtlPath']
		print('AGSPORTAL environment variable not present. Using configuration file value instead.')
	if dsPath is None:
		dsPath = config_values['esriDsPath']
		print('AGSDATASTORE environment variable not present. Using configuration file value instead.')
	
	# days filter
	days = int(config_values['filterNumberOfDays'])
	#days = 700 # temporary value
	
	# Esri logs
	if config_values['getEsriMainLogs'] == True:
		# Get the Esri things that exist on this machine...
		print('Collecting logs from Esri software...')
		
		# ArcGIS Server (and whatever else we're configured to get ...)
		gatherArcGISServer(agsPath, days, config_values)

		# Portal for ArcGIS (and whatever else we're configured to get ...)
		gatherPortal(prtlPath, days, config_values)
		
		# Data Store (and whatever else we're configured to get ...)
		gatherDataStore(dsPath, days, config_values)
	
	# Not getting Esri logs, are we getting web server access logs?	
	# We can re-use this function (in spite of the name)
	gatherNonEsriAfterEsri(config_values, days)	
	# elif config_values['getWebServerAccessLogs'] == True:
		# print('Collecting web server access logs ...')
		
		# if os.path.exists(config_values['pathWebServerAccessLogs']) == True:
			# collectWebAccessLogs(config_values['pathWebServerAccessLogs'], days)
		# else:
			# print('Web server log path does not exist or is not accessible: ' + config_values['pathWebServerAccessLogs'])
		# # Not getting Esri logs, are we getting OS logs?
	# elif config_values['getOsLogs'] == True:
		# print('Collecting OS logs ...')
		
		# if os.path.exists(config_values['pathOsLogs'] ) == True:
			# collectOsLogs(config_values['pathOsLogs'])
	
	print('### COLLECTION PROCESS COMPLETE! ###')
	
# make output dir, if it does not exist, returning full path	
def setupOutputDir():
	machineName = socket.getfqdn()
	cwd = os.getcwd()
	candidateDir = os.path.join(cwd , machineName)
	if os.path.isdir(candidateDir) == False:
		os.mkdir(candidateDir)
		print('Created output directory: ' + candidateDir)
	else:
		print('Using output directory: ' + candidateDir)
	return candidateDir
	
def runningAsAdmin():
	is_admin = False
	try:
		is_admin = os.getuid() == 0
	except AttributeError:
		is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
	return is_admin

def gatherDataStore(dsPath, days, config_values):
	if os.path.exists(dsPath):
		print('Collecting ArcGIS Data Store logs ...')
		
		collectMainDataStore(dsPath, days)
		if config_values['getEsriTomcatLogs'] == True:
			collectDsTomcatLogs(dsPath, days)			
		if config_values['getEsriServiceLogs'] == True:
			collectDsServiceLogs(dsPath, days)

		gatherNonEsriAfterEsri(config_values, days)
			
def gatherPortal(prtlPath, days, config_values):
	if os.path.exists(prtlPath):
		print('Collecting Portal for ArcGIS logs ...')
		
		collectMainPrtl(prtlPath, days)
		if config_values['getEsriTomcatLogs'] == True:
			collectPrtlTomcatLogs(prtlPath, days)			
		if config_values['getEsriServiceLogs'] == True:
			collectPrtlServiceLogs(prtlPath, days)	
		if config_values['getPrtlWebgisdrLogs'] == True:
			collectWebgisdrLogs(prtlPath, days)
		
		gatherNonEsriAfterEsri(config_values, days)

	
def gatherArcGISServer(agsPath, days, config_values):
	if os.path.exists(agsPath):
		print('Collecting ArcGIS Server logs ...')
		collectMainAgs(agsPath, days)
		if config_values['getAgsConfigStore'] == True:
			collectConfigStore(agsPath)
		if config_values['getEsriTomcatLogs'] == True:
			collectAgsTomcatLogs(agsPath, days)			
		if config_values['getEsriServiceLogs'] == True:
			collectAgsServiceLogs(agsPath, days)	
		
		gatherNonEsriAfterEsri(config_values, days)


def gatherNonEsriAfterEsri(config_values, days):
	if config_values['getOsLogs'] == True:
		if bOsLogsCollected == False:
			if os.path.exists(config_values['pathOsLogs'] ) == True:
				print('Collecting OS logs ...')
				collectOsLogs(config_values['pathOsLogs'])
	if config_values['getWebServerAccessLogs'] == True:
		if bWebServerLogsCollected == False:
			if os.path.exists(config_values['pathWebServerAccessLogs']) == True:
				print('Collecting web server access logs ...')
				collectWebAccessLogs(config_values['pathWebServerAccessLogs'], days)
			else:
				print('Web server log path does not exist or is not accessible: ' + config_values['pathWebServerAccessLogs'])
	if config_values['getWebAdaptorLogs'] == True:
		if bWebAdaptorLogsCollected == False:
			collectWebAdaptorsLogs(config_values['pathWebAdaptors'], days)
	

# read the config file and return a dictionary of settings
def read_config(configFile):
	config = configparser.ConfigParser()
	config.read(configFile)
	
	getEsriMainLogs = config.getboolean('WhatToCollect','esriMainLogs')
	getWebServerAccessLogs = config.getboolean('WhatToCollect','webServerAccessLogs')
	getOsLogs = config.getboolean('WhatToCollect','oslogs')
	getEsriServiceLogs = config.getboolean('WhatToCollect','esriservicelogs')
	getEsriTomcatLogs = config.getboolean('WhatToCollect','esritomcatlogs')
	getAgsConfigStore = config.getboolean('WhatToCollect','agsconfigstore')
	getAgsArcGisInputDirectory = config.getboolean('WhatToCollect','agsarcgisinputdirectory')
	getWebAdaptorLogs = config.getboolean('WhatToCollect','webAdaptorLogs')
	getPrtlWebgisdrLogs = config.getboolean('WhatToCollect','prtlwebgisdrlogs')
	
	filterNumberOfDays = config.get('Filters','days')
	
	pathWebServerAccessLogs = config.get('OsPaths','webserveraccesslogs')
	pathWebAdaptors = config.get('OsPaths', 'webAdaptors') # Comma delimited list of paths to the Web Adaptor(s) (not the path to the Logs subdirectory)
	pathOsLogs = config.get('OsPaths','oslogs')
	
	esriAgsPath = config.get('EsriPathsInEnvironmentVariablesDoNotExist','agsserver')
	esriPrtlPath = config.get('EsriPathsInEnvironmentVariablesDoNotExist','agsportal')
	esriDsPath = config.get('EsriPathsInEnvironmentVariablesDoNotExist','agsdatastore')
	
	config_values = {
		'getEsriMainLogs' : getEsriMainLogs,
		'getWebServerAccessLogs' : getWebServerAccessLogs,
		'getOsLogs' : getOsLogs,
		'getEsriServiceLogs' : getEsriServiceLogs,
		'getEsriTomcatLogs' : getEsriTomcatLogs,
		'getAgsConfigStore' : getAgsConfigStore,
		'getAgsArcGisInputDirectory' : getAgsArcGisInputDirectory,
		'getPrtlWebgisdrLogs' : getPrtlWebgisdrLogs,
		'getWebAdaptorLogs' : getWebAdaptorLogs,
		'filterNumberOfDays' : filterNumberOfDays,
		'pathWebServerAccessLogs' : pathWebServerAccessLogs,
		'pathOsLogs' : pathOsLogs,
		'pathWebAdaptors' : pathWebAdaptors,
		'esriAgsPath' : esriAgsPath,
		'esriPrtlPath' : esriPrtlPath, 
		'esriDsPath' : esriDsPath
	}
	
	return config_values 
	
# create the config file if it doesn't exist
def create_config():
	config = configparser.ConfigParser()
	config['WhatToCollect'] = {'esriMainLogs': True, 'webServerAccessLogs': True, 'osLogs': True, 'esriServiceLogs': True, 'esriTomcatLogs': True,'agsConfigStore': True, 'agsArcgisInputDirectory':True, 'prtlWebgisdrLogs': True, 'webAdaptorLogs' : False}
	config['Filters'] = {'days': 10}
	config['OsPaths'] = {'webServerAccessLogs': r'C:\inetpub\logs\LogFiles\W3SVC1','osLogs': r'C:\Windows\System32\winevt\Logs', 'webAdaptors': r'C:\inetpub\wwwroot\arcgis,C:\inetpub\wwwroot\server'}
	config['EsriPathsInEnvironmentVariablesDoNotExist'] =  {'AGSSERVER': r'C:\Program Files\ArcGIS\Server','AGSPORTAL': r'C:\Program Files\ArcGIS\Portal','AGSDATASTORE': r'C:\Program Files\ArcGIS\DataStore'} 
	
	configFilePath = Path('config.ini')
	if (not os.path.isfile(configFilePath)) or (not os.access(configFilePath, os.R_OK)):
		print('Writing default config.ini ... ')
		with open ('config.ini','w') as configFile:
			config.write(configFile)
	
def is_file_younger_than_x_days(file, days=7): 
	file_time = os.path.getmtime(file) 
	return ((time.time() - file_time) / 3600 < 24*days)

def collectWebAdaptorsLogs(pathWebAdaptors, days):
	webAdaptorList = pathWebAdaptors.split(',')
	for webAdaptor in webAdaptorList:
		if os.path.exists(webAdaptor):
			webAdaptorName = os.path.basename(os.path.normpath(webAdaptor))
			print ('Collecting Web Adaptor logs for ' + webAdaptorName + ' ...')
			zipFileName = r'webAdaptorLogsFor' + webAdaptorName + r'.zip'
			webAdaptorLogPath = webAdaptor + r'\Logs'
			alwaysIncludeFileList = ['']
			excludeFileExtensionsList = ['.rlock','.wlock','.lck']
			try:
				makeZip(zipFileName, webAdaptorLogPath, alwaysIncludeFileList, excludeFileExtensionsList, days)
			except Exception as error:
				print ('Unable to collect web access logs due to error', error)
		else:
			print ('Web Adaptor path does not exist or is not accessible: ' + webAdaptor)
	global bWebAdaptorLogsCollected
	bWebAdaptorLogsCollected = True

def collectWebAccessLogs(pathWebServerAccessLogs, days):
	if (os.name == 'nt'):
		alwaysIncludeFileList = ['']
		excludeFileExtensionsList = ['.rlock','.wlock','.lck']
		try:
			global bWebServerLogsCollected
			bWebServerLogsCollected = True
			makeZip('iisLogs.zip', pathWebServerAccessLogs, alwaysIncludeFileList, excludeFileExtensionsList, days)
		except Exception as error:
			print ('Unable to collect web access logs due to error', error)
	else:
		print('Only IIS log collection is supported at present')
	
def collectOsLogs(pathOsLogs):
	if (os.name == 'nt'):
		# Windows
		alwaysIncludeFileList = ['']
		excludeFileExtensionsList = ['.rlock','.wlock','.lck']
		alldays = -1
		try:
			global bOsLogsCollected
			bOsLogsCollected = True
			makeZip('eventViewLogs.zip', pathOsLogs, alwaysIncludeFileList, excludeFileExtensionsList, alldays)
		except Exception as error:
			print ('Unable to collect os logs due to error', error)
	else:
		print('Linux OS log collection not yet implemented')

def collectWebgisdrLogs(prtlPath, days):
	webgisdrLogPath = prtlPath + r'\tools\webgisdr'
	alwaysIncludeFileList = ['']
	excludeFileExtensionsList = ['.rlock','.wlock','.lck','.txt','.jar','.dll','.exe','.bat']
	try:
		makeZip('webgisdrLogs.zip', webgisdrLogPath, alwaysIncludeFileList, excludeFileExtensionsList, days) 
	except Exception as error:
		print ('Unable to collect webgisdr logs due to error', error)
	

def collectDsServiceLogs(dsPath, days):
	serviceLogDir = dsPath + r'\framework\etc\service\logs'
	alwaysIncludeFileList = ['']
	excludeFileExtensionsList = ['.rlock','.wlock','.lck','.txt']
	try:
		makeZip('dsServiceLogs.zip', serviceLogDir, alwaysIncludeFileList, excludeFileExtensionsList, days) 
	except Exception as error:
		print ('Unable to collect ArcGIS Data Store service logs due to error', error)


def collectPrtlServiceLogs(prtlPath, days):
	serviceLogDir = prtlPath + r'\framework\etc\service\logs'
	alwaysIncludeFileList = ['']
	excludeFileExtensionsList = ['.rlock','.wlock','.lck','.txt']
	try:
		makeZip('prtlServiceLogs.zip', serviceLogDir, alwaysIncludeFileList, excludeFileExtensionsList, days) 
	except Exception as error:
		print ('Unable to collect Portal for ArcGIS service logs due to error', error)

def collectAgsServiceLogs(agsPath, days):
	serviceLogDir = agsPath + r'\framework\etc\service\logs'
	alwaysIncludeFileList = ['']
	excludeFileExtensionsList = ['.rlock','.wlock','.lck','.txt']
	try:
		makeZip('agsServiceLogs.zip', serviceLogDir, alwaysIncludeFileList, excludeFileExtensionsList, days) 
	except Exception as error:
		print ('Unable to collect ArcGIS Server service logs due to error', error)

def collectDsTomcatLogs(dsPath, days):
	tomcatLogDir = dsPath + r'\framework\runtime\tomcat\logs'
	alwaysIncludeFileList = ['']
	excludeFileExtensionsList = ['.rlock','.wlock','.lck']
	try:
		makeZip('dsTomcat.zip', tomcatLogDir, alwaysIncludeFileList, excludeFileExtensionsList, days)	
	except Exception as error:
		print ('Unable to collect ArcGIS Data Store tomcat logs due to error', error)


def collectPrtlTomcatLogs(prtlPath, days):
	tomcatLogDir = prtlPath + r'\framework\runtime\tomcat\logs'
	alwaysIncludeFileList = ['']
	excludeFileExtensionsList = ['.rlock','.wlock','.lck']
	try:
		makeZip('prtlTomcat.zip', tomcatLogDir, alwaysIncludeFileList, excludeFileExtensionsList, days)	
	except Exception as error:
		print ('Unable to collect Portal for ArcGIS tomcat logs due to error', error)
		
def collectAgsTomcatLogs(agsPath, days):
	tomcatLogDir = agsPath + r'\framework\runtime\tomcat\logs'
	alwaysIncludeFileList = ['']
	excludeFileExtensionsList = ['.rlock','.wlock','.lck']
	try:
		makeZip('agsTomcat.zip', tomcatLogDir, alwaysIncludeFileList, excludeFileExtensionsList, days)	
	except Exception as error:
		print ('Unable to collect ArcGIS Server tomcat logs due to error', error)
		
def collectConfigStore(agsPath):
	# get the entire config store
	configStoreDir = None
	configStoreXml = agsPath + r'\framework\etc\config-store-connection.xml'
	tree = ET.parse(configStoreXml)
	root = tree.getroot()
	properties = root.findall(".//entry[@key='connectionString']")
	configStoreDir = properties[0].text
	
	if configStoreDir is not None:
		alwaysIncludeFileList = ['']
		excludeFileExtensionsList = ['.rlock','.wlock','.lck']
		alldays = -1
		try:
			makeZip('agsConfigStore.zip', configStoreDir, alwaysIncludeFileList, excludeFileExtensionsList, alldays)
		except Exception as error:
			print ('Unable to collect ArcGIS Server config-store due to error', error)


def collectMainDataStore(dsPath, days):
	
	# Get the main log directory from the configuration file in the AGS installation directory
	# C:\Program Files\ArcGIS\Portal\framework\etc
	logDir = None
	logSettingsFile = dsPath + r'\framework\etc\arcgis-logsettings.json'
	with open (logSettingsFile) as f:
		logSettingsFileJson = json.load(f)
		logDir = logSettingsFileJson['logDir']
	
	if logDir is not None:
		alwaysIncludeFileList = ['info.log']
		excludeFileExtensionsList = ['.rlock','.wlock','.lck'] 
		try:
			makeZip('dsMainLogs.zip',logDir,alwaysIncludeFileList,excludeFileExtensionsList,days)
		except Exception as error:
			print ('Unable to collect Portal for ArcGIS main logs due to error', error)


def collectMainPrtl(prtlPath, days):
	# Note: Sharing API log records show up in the main logs when Sharing API logging is enabled.
	
	# Get the main log directory from the configuration file in the AGS installation directory
	# C:\Program Files\ArcGIS\Portal\framework\etc
	logDir = None
	logSettingsFile = prtlPath + r'\framework\etc\arcgis-logsettings.json'
	#print(logSettingsFile)
	with open (logSettingsFile) as f:
		logSettingsFileJson = json.load(f)
		logDir = logSettingsFileJson['logDir']
		#print(logDir)
	
	if logDir is not None:
		alwaysIncludeFileList = ['info.log']
		excludeFileExtensionsList = ['.rlock','.wlock','.lck'] 
		try:
			makeZip('prtlMainLogs.zip',logDir,alwaysIncludeFileList,excludeFileExtensionsList,days)
		except Exception as error:
			print ('Unable to collect Portal for ArcGIS main logs due to error', error)

	
def collectMainAgs(agsPath, days):
	
	# Get the main log directory from the configuration file in the AGS installation directory
	# C:\Program Files\ArcGIS\Server\framework\etc
	logDir = None
	logSettingsFile = agsPath + r'\framework\etc\arcgis-logsettings.json'
	#print(logSettingsFile)
	with open (logSettingsFile) as f:
		logSettingsFileJson = json.load(f)
		logDir = logSettingsFileJson['logDir']
		#print(logDir)
	
	if logDir is not None:
		alwaysIncludeFileList = ['info.log']
		excludeFileExtensionsList = ['.rlock','.wlock','.lck'] 
		try:
			makeZip('agsMainLogs.zip',logDir,alwaysIncludeFileList,excludeFileExtensionsList,days)
		except Exception as error:
			print ('Unable to collect ArcGIS Server main logs due to error', error)

# Make a new zip file with the name zipFileToMake
#   From the LogDir
#   Include all files matching the list of names in alwaysIncludeFileList
#   Exclude all files with the extensions in the excludeFileExtensionsList
#	   After that, only include files within the number of days (-1 means all)
#	Relies upon a global variable 'outputDir' for the output location
def makeZip(zipFileToMake, logDir, alwaysIncludeFileList, excludeFileExtensionsList, days):
	
	# turn short name into full path to output directory
	zipFileToMake = os.path.join(outputDir, zipFileToMake)
	
	with ZipFile(zipFileToMake, 'w') as zip_object:
		for folder_name, sub_folders, file_names in os.walk(logDir):
			for filename in file_names:
				file_path = os.path.join(folder_name, filename)
				if (filename in alwaysIncludeFileList):
					zip_object.write(file_path)			
				else:
					fileNameBase, fileNameExtension = os.path.splitext(filename)
					if (fileNameExtension in excludeFileExtensionsList) == False:
						if (days != -1):
							if (is_file_younger_than_x_days(file_path,days)):
								zip_object.write(file_path)
						else:
							zip_object.write(file_path)


if __name__ == "__main__":
	sys.exit(main(sys.argv))
