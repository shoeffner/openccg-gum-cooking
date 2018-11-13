Filename:    Readme.txt
Authors:     Rob Ross
$Date: 2008-08-05 20:04:50 +0200 (Di, 05 Aug 2008) $: // last edit date
Description: 

Overview of Resources
---------------------
This is the Readme file for the English CCG grammar developed by the DiaSpace project
which makes use of the Generalised Upper Model for an account of semantics in general, 
and spatial semantics in particular. This directory all the resources which define the
grammar, but does not provide the actual tools to use the grammar.

The grammar relies on the OpenCCG grammar tools. These can be downloaded from: 

http://openccg.sourceforge.net/

If you are new to CCG grammars, and OpenCCG in particular, it is probably a good idea 
to have a look at the OpenCCG Getting Started guide which is available along with the 
OpenCCG distribution. 

Using the Grammar
-----------------
Once you have downloaded and successfully installed OpenCCG, you can start using the DiaSpace
grammars by opening up a command line prompt in this directory and typing 'tccg' to start the
OpenCCG interactive tool. Type "turn left" at the command line to get you started. You can 
also examine the testbed files to  get a better view of the current grammar coverage. 

The actual grammar coverage against the testbeds can be evaluated with the ccg-test tool. Our
grammar comes with a number of testbeds. To test with a given testbed, simply supply the testbed
name as an argument to ccg-test, e.g., on the command line

     ccg-test testbed-corpora.xml

Description of Files
--------------------- 
The directory contains a number of grammar and testbed definition files. See the OpenCCG 
documentation for a detailed account of the grammar definition files. The testbed used for 
evaluating the grammar is spread access a number of testbed files:

   testbed-gum.xml         : A testbed based on the examples provided in the GUM-Space documentation. 
   testbed-corpus.xml      : A testbed based on a set of tidied entries from human-human corpora.
   testbed-development.xml : A more ad-hoc testbed which was created as specific features are added
                             or investigated in the grammar.    

Testbed Results
---------------
  Testbed        Number of Entries             Number of Parse Failures
  =======        =================             =========================
  gum                 43                           1
  development        208                          11
  corpus             289                         141
