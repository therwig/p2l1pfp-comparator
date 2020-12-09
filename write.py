from utils import *

def lookup_input(obj, oi, sim_input_lookup, tk_deconv_dict):
  toPrint="\n"
  isTrk = (oi==InType.tk) # read from converter
  if isTrk:
    if obj in tk_deconv_dict:
      input_tks = tk_deconv_dict[obj] # set()
      #print ('yeee',input_tks)
      lookups={} #set()
      for itk in input_tks:
        lookups[itk]=set()
        # 96b inputs broken into 64+32          
        first64 = itk[:16]
        last64 = itk[-16:]
        if first64 in sim_input_lookup:
          lookups[itk] = sim_input_lookup[first64]
        if last64 in sim_input_lookup:
          lookups[itk] = sim_input_lookup[last64]
      if len(lookups):
        toPrint = " :: sim (input)->(clk,link)={}\n".format(lookups)
    else: 
      toPrint = " :: fail to find pre-convert track\n"
    pass
  else:
    if obj in sim_input_lookup: 
      toPrint = " :: sim (clk,link)={}\n".format(sim_input_lookup[obj])
  return toPrint

def WriteRegionizerReport(em_objs, sim_objs, reportDir, sim_input_lookup, tk_deconv_dict, printCommon=False):
  # high-level report
  '''
  Writes several reports (of various granularities) for debugging
  
  Summary: Number of matching regions for each event, for each obj type
  Summary-Obj: Breakdown of non-matching objects (evt and region level)
  '''
  
  f_all = open(reportDir+'summary.txt','w')
  f_tk = open(reportDir+'summary_tk.txt','w')
  f_em = open(reportDir+'summary_em.txt','w')
  f_ca = open(reportDir+'summary_ca.txt','w')
  f_mu = open(reportDir+'summary_mu.txt','w')
  f_o = [None] * InType.n
  f_o[InType.tk]=f_tk
  f_o[InType.em]=f_em
  f_o[InType.ca]=f_ca
  f_o[InType.mu]=f_mu

  # Check which objects match for all events
  nEvents, nRegions, _ = em_objs[0].shape
  match = np.zeros( (nEvents, nRegions, InType.n) )
  match_evt = np.zeros( (nEvents, InType.n) )
  em_only = {}
  sim_only = {}
  common = {}
  for ei in range(nEvents):
    for oi in range(InType.n):
      for ri in range(nRegions):
        comm, emOnly, simOnly = getOverlaps(em_objs[oi][ei,ri],
                                            sim_objs[oi][ei,ri])
        match[ei, ri, oi] = (len(emOnly) + len(simOnly) == 0)
        em_only[(ei, ri, oi)] = emOnly
        sim_only[(ei, ri, oi)] = simOnly
        common[(ei, ri, oi)] = comm
        # if ei+oi+ri==0:
        #   print(em_objs[oi][ei,ri])
        #   print(sim_objs[oi][ei,ri])
        #   print(comm, emOnly, simOnly, match[ei, ri, oi])
          
        # if '7EFEDBC8000B0009' in sim_objs[oi][ei,ri]:
        #   print (" got it", oi,ei,ri)
        #   print (em_objs[oi][ei,ri])
        #   print (sim_objs[oi][ei,ri])
        #   print(comm, emOnly, simOnly, match[ei, ri, oi])
      # across all regions
      comm, emOnly, simOnly = getOverlaps(em_objs[oi][ei,:],
                                          sim_objs[oi][ei,:])
      match_evt[ei, oi] = (len(emOnly) + len(simOnly) == 0)
      em_only[(ei, oi)] = emOnly
      sim_only[(ei, oi)] = simOnly
      common[(ei, oi)] = comm

  # Check number of matching objs per event
  for ei in range(nEvents):
    l="Event {} matching tk/em/ca/mu regions (of {}): "+\
      "{:0>2.0f}/{:0>2.0f}/{:0>2.0f}/{:0>2.0f}\n"
    f_all.write(l.format(ei, nRegions,
               match[ei, :, InType.tk].sum(),
               match[ei, :, InType.em].sum(),
               match[ei, :, InType.ca].sum(),
               match[ei, :, InType.mu].sum()))

    for oi in range(InType.n):
      #f_o[oi].write("Event {}: {} regions match \n".format(ei, int(match[ei, :, oi].sum())))
      l="Event {:2d} \n" #({:3d} common, {:3d} emulator-only, {:3d} sim-only)\n"
      f_o[oi].write(l.format(ei))
      #, len(common[(ei, oi)]),len(em_only[(ei, oi)]),len(sim_only[(ei, oi)])))

      if match[ei, :, oi].sum():
          f_o[oi].write("  Found {} non-matching regions\n".format(int(match[ei, :, oi].sum())))
      for ri in range(nRegions):
        if match[ei, ri, oi] and not printCommon: continue
        l="  Evt {:2d} Region {:2d} ({:2d} common, {:2d} emulator-only, {:2d} sim-only)\n"
        f_o[oi].write(l.format(ei, ri, len(common[(ei, ri, oi)]),
                               len(em_only[(ei, ri, oi)]),
                               len(sim_only[(ei, ri, oi)])))

        if len(em_only[(ei, ri, oi)]): f_o[oi].write("    Emulator-only:\n")
        for obj in em_only[(ei, ri, oi)]:
          l="      {} :: pt/eta/phi = {:4d} {:4d} {:4d}"
          ll = lookup_input(obj, oi, sim_input_lookup, tk_deconv_dict)
          f_o[oi].write(l.format(obj,*GetPtEtaPhi(obj, oi))+ll)

        if len(sim_only[(ei, ri, oi)]): f_o[oi].write("    Simulation-only:\n")
        for obj in sim_only[(ei, ri, oi)]:
          l="      {} :: pt/eta/phi = {:4d} {:4d} {:4d}"
          ll = lookup_input(obj, oi, sim_input_lookup, tk_deconv_dict)
          f_o[oi].write(l.format(obj,*GetPtEtaPhi(obj, oi))+ll)

        if printCommon:
          if len(common[(ei, ri, oi)]): f_o[oi].write("    Common:\n")
          for obj in common[(ei, ri, oi)]:
            l="      {} :: pt/eta/phi = {:4d} {:4d} {:4d}"
            ll = lookup_input(obj, oi, sim_input_lookup, tk_deconv_dict)
            f_o[oi].write(l.format(obj,*GetPtEtaPhi(obj, oi))+ll)

  # print( "Total matches?", GetPassFail(match) )
  # print( "Track matches?", GetPassFail(match[:,:,0]) )
  # print( "EM matches?", GetPassFail(match[:,:,1]) )
  # print( "Calo matches?", GetPassFail(match[:,:,2]) )
  # print( "Muon matches?", GetPassFail(match[:,:,3]) )

  f_all.close()
  f_tk.close()
  f_em.close()
  f_ca.close()
  f_mu.close()



def WriteCounts(fname, objs):
  '''
  Print counts for a set of objects
  '''
  
  f = open(fname,'w')

  # Check which objects match for all events
  nEvents, nRegions, _ = objs[0].shape
  maxs = [objs[i].shape[-1] for i in range(InType.n)]
  counts = np.zeros( (InType.n,nEvents,nRegions) )

  # for oi in range(InType.n):
  #   for ei in range(nEvents):
  #     for ri in range(nRegions):
  #       nonZero = sum([isNotZeroOrVtx(x) for x in objs[oi][ei,ri]])
  #       counts[oi,ei,ri] = nonZero

  for ei in range(nEvents):
    f.write("Event {}\n".format(ei))
    for ri in range(nRegions):

      # count objects
      overflow=False
      for oi in range(InType.n):
        nonZero = sum([isNotZeroOrVtx(x) for x in objs[oi][ei,ri]])
        counts[oi,ei,ri] = nonZero
        if int(nonZero) >= maxs[oi]: 
          overflow=True

      # write to file
      l=" Region {:2d} with #tk/em/ca/mu counts " +\
            "{:0>2.0f}/{:0>2.0f} {:0>2.0f}/{:0>2.0f} " +\
            "{:0>2.0f}/{:0>2.0f} {:0>2.0f}/{:0>2.0f}"
      l += ("  <-- potential overflow\n" if overflow else "\n")
      f.write(l.format(ri,
                       counts[0,ei,ri],maxs[0],
                       counts[1,ei,ri],maxs[1],
                       counts[2,ei,ri],maxs[2],
                       counts[3,ei,ri],maxs[3]))
  f.close()


def WriteForTTree(fname, objs):  
  f = open(fname,'w')

  # Check which objects match for all events
  nEvents, nRegions, _ = objs[0].shape

  f.write("oi:ei:ri:pt:eta:phi\n")

  for oi in range(InType.n):
    for ei in range(nEvents):
      for ri in range(nRegions):
        for o in objs[oi][ei,ri]:
          if isNotZeroOrVtx(o):
            pt, eta, phi = GetPtEtaPhi(o, oi)
            l="{} {} {} {} {} {}\n".format(oi,ei,ri,pt,eta,phi)
            f.write(l)
  f.close()
