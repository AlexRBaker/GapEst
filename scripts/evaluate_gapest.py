import sys,os
import matplotlib.pyplot as plt
import random
import numpy as np

def AlignContigs(ref,query,outfolder):
    
    #### Do nucmer alignment plus tiling of contigs onto genome###
    print "nucmer -mum -c 65 -p nucmer "+ref+' '+query
    assembler = query.split('/')[-2]
    os.popen("nucmer -mum -c 65 -p nucmer "+ref+' '+query)
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)

    print "show-tiling nucmer.delta"
    outfile = os.path.join(outfolder, 'truegaps.agf')
    os.popen("show-tiling -c -g -1 nucmer.delta > "+outfile )
    agf_file = open(outfile,'r')
    
    #os.remove('nucmer.delta')
    return(agf_file,assembler)

def GetGaps(agf_file,assembler,outfolder):
    #### Create our out file from the .pgf file generated by nucmer ###
    outfile = open( os.path.join(outfolder, 'truegaps.gaps'),'w')
    prev_cont_id = None
    sec_prev_cont_id = None
    prev_gap = 0
    for line in agf_file:
        if line[0] == '>':
            continue
        columns = line.split('\t')
        align_cov = columns[4]
        perc_id = columns[5]
        if float(align_cov) > 90 and float(perc_id) > 90:
            cont_id = columns[7].strip()
            gap = columns[2].strip()
            if prev_cont_id and int(prev_gap) < 3600 + 2*300 :
                print >>outfile, prev_cont_id.strip()+'\t'+cont_id+'\t'+prev_gap
                gap2 = int(sec_prev_gap)+prev_cont_len+ int(prev_gap)
                if sec_prev_cont_id and gap2 < 3600 + 2*300 :
                    print >>outfile, sec_prev_cont_id.strip()+'\t'+cont_id+'\t'+str(gap2)
            sec_prev_cont_id =  prev_cont_id
            prev_cont_id = cont_id 
            sec_prev_gap = prev_gap
            prev_cont_len = int(columns[3])
            prev_gap = gap
        else: 
            prev_cont_id = None
    return()

def GetGapsOfScaffolder(scaffolds,contigs):
    def AlignContigsofScaf(ref,query):
        
        #### Do nucmer alignment plus tiling of contigs onto genome###
        print "nucmer -mum -c 65 -p nucmer "+ref+' '+query
        assembler = query.split('/')[-2]
        os.popen("nucmer -mum -c 65 -p nucmer "+ref+' '+query)
        try:
            os.mkdir('SOPRAGaps/'+assembler)
        except OSError:
            #directory is already created
            pass
        print "show-tiling nucmer.delta"
        os.popen("show-tiling nucmer.delta > SOPRAGaps/"+assembler+'/'+assembler+'.agf' )
        agf_file = open("SOPRAGaps/"+assembler+'/'+assembler+'.agf','r')
        
        #os.remove('nucmer.delta')
        return(agf_file,assembler)
    
    def GetGapsofScaf(agf_file,assembler):
        #### Create our out file from the .pgf file generated by nucmer ###
        outfile = open("SOPRAGaps/"+assembler+'/SOPRA.gaps','w')
        prev_cont_id = None
        #sec_prev_cont_id = None
        prev_gap = 0
        for line in agf_file:
            if line[0] == '>':
                prev_cont_id = None
                #sec_prev_cont_id = None
                prev_gap = 0
                continue
            columns = line.split('\t')
            align_cov = columns[4]
            perc_id = columns[5]
            if float(align_cov) > 90 and float(perc_id) > 90:
                cont_id = columns[7].strip()
                gap = columns[2].strip()
                if prev_cont_id and int(prev_gap) < 3600 + 2*300 :
                    print >>outfile, prev_cont_id.strip()+'\t'+cont_id+'\t'+prev_gap
                    #gap2 = int(sec_prev_gap)+prev_cont_len+ int(prev_gap)
                    #if sec_prev_cont_id and gap2 < 3600 + 2*300 :
                    #    print >>outfile, sec_prev_cont_id.strip()+'\t'+cont_id+'\t'+str(gap2)
                #sec_prev_cont_id =  prev_cont_id
                prev_cont_id = cont_id 
                #sec_prev_gap = prev_gap
                #prev_cont_len = int(columns[3])
                prev_gap = gap
            else: 
                prev_cont_id = None
        return()
    (agf_file,assembler) = AlignContigsofScaf(scaffolds,contigs)
    GetGapsofScaf(agf_file,assembler)
    
    return()

def MapWithBWA(PE1,PE2,contigs,assembler):
    os.popen('bwa index '+contigs)
    os.popen('bwa aln '+contigs+ ' '+PE1+'> '+PE1+'.sai')
    os.popen('bwa aln '+contigs+ ' '+PE2+'> '+PE2+'.sai')
    os.popen('bwa sampe -s '+contigs+' '+PE1+'.sai '+PE2+'.sai '+PE1+' '+PE2+' > mapped.sam')
    os.popen('mv mapped.sam Gaps/'+assembler+'/')
    return()

def GetGapDifference(true_gap_file,assembly_gap_file,assembler,outfolder):
    def GetGaps(gapfile):
        gapdict = {}
        gap_file = open(gapfile,'r')
        #skip header
        gap_file.readline()
        for line in gap_file:
            contig1 = line.split()[0].strip()
            contig2 = line.split()[1].strip()
            #if line.split()[4].strip()[:2] == 'w1':
            #    print line
            #    continue
            #print line
            try:
                gap = int(line.split()[2].strip())
            except ValueError:
                continue
            gapdict[(contig1,contig2)] = gap
            gapdict[(contig2,contig1)] = gap
        return(gapdict)
            
    true_gap_dict = GetGaps(true_gap_file)    
    assembly_gap_dict = GetGaps(assembly_gap_file) 
    true = []
    est = [] 
    nr_gaps = 0
    max_min_obs = [0,0]
    for cont_pair in true_gap_dict:
        gap = assembly_gap_dict.get(cont_pair, None)
        if gap:
            #print 'GapEST:' ,cont_pair, gap , 'True:',  true_gap_dict[cont_pair]
            est.append(gap)
            true.append(true_gap_dict[cont_pair])
            nr_gaps +=1
            if gap > max_min_obs[1]:
                max_min_obs[1] = gap
            if true_gap_dict[cont_pair] > max_min_obs[1]:
                max_min_obs[1] = true_gap_dict[cont_pair]
            if gap < max_min_obs[0]:
                max_min_obs[0] = gap
            if true_gap_dict[cont_pair] < max_min_obs[0]:
                max_min_obs[0] = true_gap_dict[cont_pair]
                


    ## Dot plot ##
    
    p1 = plt.plot(true, est, 'o',color = 'black')
    x=[]
    y=[]
    for i in range(max_min_obs[0]-100,max_min_obs[1]+100):
        x.append(i)
        y.append(i)
    #plt.legend([len( p1)], ["nr of estimations"])
    plt.ylabel('Estimated gap') 
    plt.xlabel('True gap')  
    plt.title(assembler)
    plt.legend( )
    #p2 =plt.plot(x, y, '--', color = 'grey',)
    X_plot = np.linspace(-500,5000,100)
    p2 =plt.plot(X_plot, X_plot, '--', color = 'grey',)
    s = 'Number of observations = '+str(len(true)/2)
    plt.text(max_min_obs[0]+100, max_min_obs[1]-100, s, fontdict=None)

    
    # ############
    # # heat dot plot

    # from scipy.stats import gaussian_kde

    x = np.array(true)
    y = np.array(est)
    # # Generate fake data
    # #x = np.random.normal(size=1000)
    # #y = x * 3 + np.random.normal(size=1000)

    # # Calculate the point density
    # xy = np.vstack([x,y])
    # z = gaussian_kde(xy)(xy)

    # fig, ax = plt.subplots()
    # ax.scatter(x, y, c=z, s=100, edgecolor='')
    # plt.savefig(os.path.join(outfolder,'heat_'+assembler+'.png'))
    # ###########

    ########
    # R-squared
    import scikits.statsmodels.api as sm
    #fig, ax = plt.subplots()
    results = sm.OLS(y,sm.add_constant(x)).fit()

    print results.summary()

    #plt.scatter(x,y)

    X_plot = np.linspace(-500,5000,100)
    plt.plot(X_plot, X_plot*results.params[0] + results.params[1])


    plt.savefig(os.path.join(outfolder,assembler+'.png'))
    print 'Nr gaps: ', nr_gaps/2
    #plt.savefig(os.path.join(outfolder,'Rsquared_'+assembler+'.png'))   


    return()

def GetGapDifferenceAll(true_gap_file,assembly_gap_file,sopra_gap_file,assembler):
    def GetGaps(gapfile):
        gapdict = {}
        gap_file = open(gapfile,'r')
        for line in gap_file:
            contig1 = line.split()[0].strip()
            contig2 = line.split()[1].strip()
            gap = int(line.split()[2].strip())
            gapdict[(contig1,contig2)] = gap
            gapdict[(contig2,contig1)] = gap
        return(gapdict)
            
    true_gap_dict = GetGaps(true_gap_file)    
    assembly_gap_dict = GetGaps(assembly_gap_file) 
    sopra_gap_dict = GetGaps(sopra_gap_file)
    true = []
    est = [] 
    sopra_est = []
    nr_gaps = 0
    max_min_obs = [0,0]
    for cont_pair in true_gap_dict:
        gap = assembly_gap_dict.get(cont_pair, None)
        sopra_gap = sopra_gap_dict.get(cont_pair,None)
        if gap and sopra_gap:
            #print 'GapEST:' ,cont_pair, gap , 'True:',  true_gap_dict[cont_pair]
            est.append(gap)
            sopra_est.append(sopra_gap)
            true.append(true_gap_dict[cont_pair])
            nr_gaps +=1
            if gap > max_min_obs[1]:
                max_min_obs[1] = gap
            if true_gap_dict[cont_pair] > max_min_obs[1]:
                max_min_obs[1] = true_gap_dict[cont_pair]
            if sopra_gap > max_min_obs[1]:
                max_min_obs[1] = sopra_gap
            if gap < max_min_obs[0]:
                max_min_obs[0] = gap
            if true_gap_dict[cont_pair] < max_min_obs[0]:
                max_min_obs[0] = true_gap_dict[cont_pair]
            if sopra_gap < max_min_obs[0]:
                max_min_obs[0] = sopra_gap                
            
    ## Dot plot ##
    
    p1 = plt.plot(true, est, 'o',color = 'blue')
    p2 = plt.plot(true, sopra_est, 'x',color = 'red')
    x=[]
    y=[]
    for i in range(max_min_obs[0]-100,max_min_obs[1]+100):
        x.append(i)
        y.append(i)
    #plt.legend([len( p1)], ["nr of estimations"])
    plt.ylabel('Estimated gap') 
    plt.xlabel('True gap')  
    plt.title(assembler)
    plt.legend( )
    p3 =plt.plot(x, y, '-', color = 'green')
    s = 'Number of observations = '+str(len(true)/2)
    plt.text(max_min_obs[0]+100, max_min_obs[1]-100, s, fontdict=None)
    plt.savefig(assembler+'.png')
    print 'Nr gaps: ', nr_gaps/2
    
    return()

def RunGapEst(contigfile,samfile,outdirectry, naive=False, bayesian=False):
    if not os.path.exists(outdirectry):
        os.makedirs(outdirectry)
    outfile = os.path.join(outdirectry,'GapEst.gaps')
        # setting -r to read_length - softclipps = 100-70
    os.popen("python /Users/ksahlin/Documents/workspace/GapEst/src/Main.py 1 -c "+contigfile + ' -f ' +samfile +' -m 2000 -s 500 -e 10 -r 30  > '+ outfile ) #--bayesian 1
    return()

def ShuffleContigs(contigfile,assembler):
    ## read in contigs
    contigs = open(contigfile,'r')
    cont_dict={}
    k=0
    temp=''
    accession=''
    for line in contigs:
        if line[0]=='>' and k==0:
            accession=line[1:].strip().split()[0]
            cont_dict[accession]=''
            k+=1
        elif line[0]=='>':
            cont_dict[accession]=temp
            temp=''
            accession=line[1:].strip().split()[0]
        else:
            temp+=line.strip()
    cont_dict[accession]=temp
    #randomize
    items = cont_dict.items()
    random.shuffle(items)
    ##print out scrambled contigs
    scr_cont = open('Gaps/'+assembler+'/contigs_scrambled.fa','w')
    for acc,cont in items:
        print >>scr_cont, '>'+acc+'\n'+cont
        
    return()
def RunSOPRA(contigs,PE1,PE2,outfolder):
    #prep step
    os.popen("perl ../../SOPRA_v1.4.6/combiner.pl "+PE1+' '+PE2+' > ../../SOPRA_v1.4.6/PE.fasta' )
    os.popen("perl ../../SOPRA_v1.4.6/source_codes_v1.4.6/SOPRA_with_prebuilt_contigs/s_prep_contigAseq_v1.4.6.pl -contig "+contigs +' -mate ../../SOPRA_v1.4.6/PE.fasta -a '+ outfolder)
    #mapping step 
    os.popen('bwa index '+outfolder+ 'contigs_sopra.fasta')
    os.popen('bwa aln '+outfolder+ 'contigs_sopra.fasta ../../SOPRA_v1.4.6/PE_sopra.fasta > ../../SOPRA_v1.4.6/PE_sopra.fasta.sai')
    os.popen('bwa samse '+outfolder+'contigs_sopra.fasta ../../SOPRA_v1.4.6/PE_sopra.fasta.sai ../../SOPRA_v1.4.6/PE_sopra.fasta > ../../SOPRA_v1.4.6/mapped.sam')
    print 'perl  ../../SOPRA_v1.4.6/source_codes_v1.4.6/SOPRA_with_prebuilt_contigs/s_parse_sam_v1.4.6.pl -sam ../../SOPRA_v1.4.6/mapped.sam -a ../../SOPRA_v1.4.6/'
    os.popen( 'perl  ../../SOPRA_v1.4.6/source_codes_v1.4.6/SOPRA_with_prebuilt_contigs/s_parse_sam_v1.4.6.pl -sam ../../SOPRA_v1.4.6/mapped.sam -a ../../SOPRA_v1.4.6/')
    print 'perl ../../SOPRA_v1.4.6/source_codes_v1.4.6/SOPRA_with_prebuilt_contigs/s_read_parsed_sam_v1.4.6.pl -parsed ../../SOPRA_v1.4.6/mapped.sam_parsed -d 3600 -a ../../SOPRA_v1.4.6/'
    os.popen('perl ../../SOPRA_v1.4.6/source_codes_v1.4.6/SOPRA_with_prebuilt_contigs/s_read_parsed_sam_v1.4.6.pl -parsed ../../SOPRA_v1.4.6/mapped.sam_parsed -d 3600 -a ../../SOPRA_v1.4.6/')
    print 'perl ../../SOPRA_v1.4.6/source_codes_v1.4.6/SOPRA_with_prebuilt_contigs/s_scaf_v1.4.6.pl -w 5 -o ../../SOPRA_v1.4.6/orientdistinfo_c5 -a ../../SOPRA_v1.4.6/'
    os.popen('perl ../../SOPRA_v1.4.6/source_codes_v1.4.6/SOPRA_with_prebuilt_contigs/s_scaf_v1.4.6.pl -w 5 -o ../../SOPRA_v1.4.6/orientdistinfo_c5 -a ../../SOPRA_v1.4.6/')
    return()

if __name__ == '__main__':
    import sys
    if sys.argv[1] == '--help':
        print 'Usage\n\n'
        print 'python GetGaps.py --getgaps <ref> <query> <outfolder>:\t gives gaps between all successive aligned contig on a reference genome'
        print 'python GetGaps.py --getsopragaps <Scaffolds> <contigs>:\t gives gaps between all successive aligned contig onto the scaffolds create by sopra.'
        print 'python GetGaps.py --comparegaps <true_gappairs> <inferred_gap_pairs> <assembler> <outfolder>:\t outputs a dot plot with the difference between the true and the inferred gaps'
        print 'python GetGaps.py --comparegapsall <true_gappairs> <inferred_gap_pairs gap est> <inferred gap pairs sopra> <assembler>:\t outputs a dot plot with the difference between the true and the inferred gaps'
        print 'python GetGaps.py --rungapest <contig file> <BAM file> <outfolder>:\t runs and outputs all gap estimations'
        print 'python GetGaps.py --map <PE1> <PE2> <ref> <assembler>:\t runs and outputs all gap estimations'
        print 'python GetGaps.py --runsopra <contig file> <PE1> <PE2> <outfolder>:\t runs and outputs all gap estimations from sopra'
        print 'python GetGaps.py --shuffle <contig file> <assembler>:\t shuffles contigs in contig file'
    if sys.argv[1]=='--getgaps':
        if not os.path.exists(sys.argv[4]):
            os.makedirs(sys.argv[4])
        agf_file ,assembler = AlignContigs(sys.argv[2],sys.argv[3],sys.argv[4])
        GetGaps(agf_file,assembler,sys.argv[4])
    if sys.argv[1]=='--getsopragaps':
        GetGapsOfScaffolder(sys.argv[2],sys.argv[3])
    if sys.argv[1]=='--comparegapsall':
        GetGapDifferenceAll(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
    if sys.argv[1]=='--comparegaps':
        GetGapDifference(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
    if sys.argv[1]=='--map':
        MapWithBWA(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
        
    if sys.argv[1]=='--rungapest':
        RunGapEst(sys.argv[2],sys.argv[3],sys.argv[4])
    if sys.argv[1]=='--runsopra':
        RunSOPRA(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5]) 
    if sys.argv[1] =='--shuffle':
        ShuffleContigs(sys.argv[2],sys.argv[3])       
   

