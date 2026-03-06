from csmp.precompiler import Precompiler



if __name__ == '__main__':
            
    mdl = Precompiler()
    mdl.compile("./models/test.csm.py")
    mdl.printSummary()
    # mdl.writeTemplate()
    # print("\n", '-'*80, '\n')
    mdl.saveListFile(True)
    # print("\n", '-'*80, '\n')
    # mdl.debugSegmentation()