#!/usr/bin/env python
#
# Starka
# Copyright (c) 2009-2014 Illumina, Inc.
#
# This software is provided under the terms and conditions of the
# Illumina Open Source Software License 1.
#
# You should have received a copy of the Illumina Open Source
# Software License 1 along with this program. If not, see
# <https://github.com/sequencing/licenses/>
#

"""
This script configures the de-novo small variant calling workflow
"""

import os,sys

scriptDir=os.path.abspath(os.path.dirname(__file__))
scriptName=os.path.basename(__file__)
workflowDir=os.path.abspath(os.path.join(scriptDir,"@THIS_RELATIVE_PYTHON_LIBDIR@"))
templateConfigDir=os.path.abspath(os.path.join(scriptDir,'@THIS_RELATIVE_CONFIGDIR@'))

version="@STARKA_FULL_VERSION@"


sys.path.append(workflowDir)

from starkaOptions import StarkaWorkflowOptionsBase
from configureUtil import BamSetChecker, groomBamList, OptParseException, joinFile, checkTabixListOption
from makeRunScript import makeRunScript
from inovoWorkflow import InovoWorkflow
from workflowUtil import ensureDir



class InovoWorkflowOptions(StarkaWorkflowOptionsBase) :

    def workflowDescription(self) :
        return """Version: %s

This script configures the Inovo de-novo small variant calling pipeline.
You must specify BAM file(s) for the proband and additional related samples.
""" % (version)


    def addWorkflowGroupOptions(self,group) :
        group.add_option("--probandAlignmnet", type="string",dest="probandBamList",metavar="FILE", action="append",
                         help="Proband BAM file. [required] (no default)")
        group.add_option("--parentAlignment", type="string",dest="parentBamList",metavar="FILE", action="append",
                          help="BAM file for a parent sample. (no default, submit argument one time for each parent)")
        group.add_option("--siblingAlignment", type="string",dest="siblingBamList",metavar="FILE", action="append",
                          help="BAM file for a sibling sample. (no default, submit argument one time for each sibling)")
#        group.add_option("--isWriteCallableRegion", action="store_true",
#                         help="Write out a bed file describing de-novo callable regions of the genome")

        StarkaWorkflowOptionsBase.addWorkflowGroupOptions(self,group)


    def getOptionDefaults(self) :

        self.configScriptDir=scriptDir
        defaults=StarkaWorkflowOptionsBase.getOptionDefaults(self)

        configDir=os.path.abspath(os.path.join(scriptDir,"@THIS_RELATIVE_CONFIGDIR@"))
        assert os.path.isdir(configDir)

        defaults.update({
            'runDir' : 'InovoWorkflow',
            'isWriteCallableRegion' : False
            })
        return defaults



    def validateAndSanitizeExistingOptions(self,options) :

        StarkaWorkflowOptionsBase.validateAndSanitizeExistingOptions(self,options)
        groomBamList(options.probandBamList,"proband sample")
        groomBamList(options.parentBamList, "parent sample")
        groomBamList(options.siblingBamList, "siblin sample")



    def validateOptionExistence(self,options) :

        StarkaWorkflowOptionsBase.validateOptionExistence(self,options)

        if len(options.probandBamList) != 1 :
            raise OptParseException("Must specify one proband sample BAM/CRAM file")

        if len(options.parentBamList) != 2 :
            raise OptParseException("Must specify two parent sample BAM/CRAM files")

        bcheck = BamSetChecker()
        bcheck.appendBams(options.probandBamList,"proband")
        bcheck.appendBams(options.parentBamList,"parent")
        bcheck.appendBams(options.siblingBamList,"sibling",isAllowEmpty=True)
        bcheck.check(options.samtoolsBin,
                     options.referenceFasta)

def main() :

    primarySectionName="inovo"
    options,iniSections=InovoWorkflowOptions().getRunOptions(primarySectionName,
                                                               version=version)

    # we don't need to instantiate the workflow object during configuration,
    # but this is done here to trigger additional parameter validation:
    #
    InovoWorkflow(options,iniSections)

    # generate runscript:
    #
    ensureDir(options.runDir)
    scriptFile=os.path.join(options.runDir,"runWorkflow.py")

    makeRunScript(scriptFile,os.path.join(workflowDir,"inovoWorkflow.py"),"InovoWorkflow",primarySectionName,iniSections)

    notefp=sys.stdout
    notefp.write("""
Successfully created workflow run script.
To execute the workflow, run the following script and set appropriate options:

%s
""" % (scriptFile))


if __name__ == "__main__" :
    main()