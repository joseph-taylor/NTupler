#!/usr/bin/python

import subprocess
import os
import sys
import datetime

# Instructions:
# 1. Compile the code you wish to run
# 2. Set the USER INPUTS for this script
# 3. Run this script $ ./submitCondorNtupleJobs_VJ.py or $ python $CMSSW_BASE/src/NTupler/PATNTupler/main/submitCondorNtupleJobs_VJ.py
# 4. cd into the outputDirectory/tmp and run the condor job


###########################################################################################################
############## USER INPUTS ################################################################################
###########################################################################################################
###########################################################################################################
###########################################################################################################

executable = "nTupAnaNMSSM" # wrt 'main' directory
code = "mainNMSSM.cc" # wrt 'main' directory
inputFileListPath = "/home/ppd/xap79297/CMSSW_8_0_21/src/NTupler/PATNTupler/fileLists/TTJets_HT-2500toInf_v2.list"
outputDirectory = "/opt/ppd/scratch/xap79297/Analysis_boostedNmssmHiggs/flatTrees_2017_05_18/TTJets_HT2500toInf" # has to be the full path
filesPerJob = 2
jsonFile = ""
logDirectoryBase = "/opt/ppd/scratch/xap79297/jobLogs/flatTrees/"

###########################################################################################################
###########################################################################################################
###########################################################################################################
###########################################################################################################
###########################################################################################################
###########################################################################################################
###########################################################################################################


if outputDirectory[-1] == "/":
    outputDirectory = outputDirectory[:-1]

dataname = ""
for iChar in range (len(outputDirectory)-1, 0, -1):
    if outputDirectory[iChar] == "/":
        dataname = outputDirectory[iChar+1:]
        break
dataname = dataname + "_" + '{:%Y_%m_%d-%H_%M_%S}'.format(datetime.datetime.now())
logDirectory = os.path.join(logDirectoryBase,dataname)

baseDir = os.environ['CMSSW_BASE']
if len(baseDir) == 0:
    print "You are not in a CMSSW environment"
    print "Exiting..."
    sys.exit()
# if baseDir[0:4] == "/net":
#     baseDir = baseDir[4:]

# Check that the output directory does not already exist
if os.path.isdir(outputDirectory) == True:
    print "The output directory, " + outputDirectory + " already exists"
    print "Exiting..."
    sys.exit()
# Check that the log directory does not already exist
# if os.path.isdir(logDirectory) == True:
#     print "The log directory, " + logDirectory + " already exists"
#     print "Exiting..."
#     sys.exit()
# Check that the fileList exists before continuing
if os.path.exists(inputFileListPath) == False:
    print "The fileList, " + inputFileListPath + " doesn't exist"
    print "Exiting..."
    sys.exit()

# Make the new directory(s)
os.system("mkdir -p %s" % outputDirectory)
os.system("mkdir %s/tmp" % outputDirectory)
os.system("cp %s/src/NTupler/PATNTupler/main/%s %s" % (baseDir,code,outputDirectory))
os.system("cp %s %s" % (inputFileListPath,outputDirectory))
os.system("mkdir -p %s" % logDirectory)


# Create list of files for each job
inputFileList = open(inputFileListPath).readlines()

numFilesInJob = 1
tmpList = []
filesPerJobList = []
for line in inputFileList:
    tmpList.append(line)
    if (numFilesInJob == filesPerJob):
        filesPerJobList.append(tmpList)
        numFilesInJob = 1
        tmpList = []
    else:
        numFilesInJob = numFilesInJob + 1
if (len(tmpList) > 0):
    filesPerJobList.append(tmpList)


# Create a bash script that will submit all the jobs
submitCondorJobsFilename = outputDirectory + "/tmp/submitCondorJobs_" + executable + ".sh"
submitCondorJobs = open(submitCondorJobsFilename,"w")


# Create the executable script for each job
jobNum = 0
for jobList in filesPerJobList:
    
    jobListFileName = outputDirectory + "/tmp/job_" + str(jobNum) + ".list"
    jobListFile = open(jobListFileName,"w")
    for line in jobList:
        jobListFile.write(line)

    shellJobName = outputDirectory + "/tmp/job_" +str(jobNum) + ".sh"
    shellJob = open(shellJobName,"w")

    cmd = "#!/bin/bash\n"
    # cmd += "export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch/\n"
    # cmd += "source $VO_CMS_SW_DIR/cmsset_default.sh\n"
    # cmd += "cd " + baseDir + "/src/\n"
    # cmd += "eval `scramv1 runtime -sh`\n"
    cmd += baseDir + "/src/NTupler/PATNTupler/main/" + executable + " flatTree_" + str(jobNum) + ".root " + jobListFileName + " batch " + jsonFile + "\n"
    cmd += "cp flatTree_" + str(jobNum) + ".root ../../.\n"
    # cmd += baseDir + "/src/NTupler/PATNTupler/main/" + executable + " /scratch/flatTree_" + str(jobNum) + ".root " + jobListFileName + " batch " + jsonFile + "\n"
    # cmd += "mv  /scratch/flatTree_" + str(jobNum) + ".root " + outputDirectory + "\n"


    shellJob.write(cmd)
    os.chmod(shellJobName, 0755)

    # Create htcondor config files for each individual job submission
    condorFileName = outputDirectory + "/tmp/job_" + str(jobNum) + ".condor"
    condorFile = open(condorFileName,"w")
    condorTemplate = open("%s/src/NTupler/PATNTupler/batchJobs/template_VJ.condor" % baseDir)
    condorLineList = condorTemplate.readlines()
    for condorLine in condorLineList:
        jobid = "job_" + str(jobNum)
        condorLine = condorLine.replace("REPLACE_WITH_JOBID",jobid)
        condorLine = condorLine.replace("REPLACE_LOG_DIRECTORY",logDirectory)
        condorFile.write(condorLine)
    os.chmod(condorFileName,0755)

    submitCondorJobs.write("condor_submit job_" + str(jobNum) + ".condor" + "\n")
    jobNum = jobNum + 1

os.chmod(submitCondorJobsFilename,0755)