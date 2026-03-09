from csmp.precompiler import Precompiler



if __name__ == '__main__':
    from csmp.precompiler.nodeWraps import NodeWrap
            
    mdl = Precompiler()
    mdl.compile("./models/reserve_Goudriaan.csm.py")
    mdl.printSummary()
    # print("\n", '-'*80, '\n')
    mdl.writeListFile()
    print("\n", '-'*80, '\n')
    mdl.writeTemplate()
    # mdl.debugSegmentation()
    # for o in sorted(NodeWrap.objects, key=lambda o: str(o)):
    #     print(o)    