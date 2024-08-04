This Python script is similar to the Java app 'logCollector'.  It is the eventual replacement for that Java app.

Run this tool as a local machine admin to collect a wide variety of Esri-related log types from a machine.  By default, the script will gather the last 10 days of logs and place them in a subdirectory named for the machine.  If you wish to use a custom configuration file to control the number of days or other aspects of log collection, the script allows you to specify a -f <config file name> parameter.  A default configuration file is created if a custom one is not supplied.

At present, the script only supports Windows.  However, I will extend support for Linux shortly.

Please be in contact with questions or feedback: dkrouk@esri.com

