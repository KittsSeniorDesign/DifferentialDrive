import subprocess

class ExporterLauncher(subprocess.Popen):
    def __init__( self, logFileName, *args, **kwargs ):
        logFile = open( logFileName, 'w+b' )
        kwargs['stdout'] = logFile
        kwargs['stderr'] = logFile
        super(ExporterLauncher, self).__init__( *args, **kwargs )
        print('Exporter launched.')

exporter = ExporterLauncher('dtexporter.log', ('java','-jar','build/DataturbineExporter.jar','localhost:3333','/tmp/dtexport.sock','decabot-x'))
