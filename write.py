from utils import *

def WriteRegionizerReport(em_objs, sim_objs, reportDir, sim_input_lookup):
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
      l="Event {:2d} ({:3d} common, {:3d} emulator-only, {:3d} sim-only)\n"
      f_o[oi].write(l.format(ei, len(common[(ei, oi)]),
                               len(em_only[(ei, oi)]),
                               len(sim_only[(ei, oi)])))

      if match[ei, :, oi].sum():
          f_o[oi].write("  Found {} non-matching regions\n".format(int(match[ei, :, oi].sum())))
      for ri in range(nRegions):
        if match[ei, ri, oi]: continue
        l="  Region {:2d} ({:2d} common, {:2d} emulator-only, {:2d} sim-only)\n"
        f_o[oi].write(l.format(ri, len(common[(ei, ri, oi)]),
                               len(em_only[(ei, ri, oi)]),
                               len(sim_only[(ei, ri, oi)])))
        if len(em_only[(ei, ri, oi)]): f_o[oi].write("    Emulator-only:\n")
        for obj in em_only[(ei, ri, oi)]:
            l="      {} :: pt/eta/phi = {:4d} {:4d} {:4d}"
            if obj in sim_input_lookup: 
              ll=" :: sim (clk,link)={}\n".format(sim_input_lookup[obj])
            else: 
              ll="\n"
            f_o[oi].write(l.format(obj,*GetPtEtaPhi(obj, oi))+ll)
        if len(sim_only[(ei, ri, oi)]): f_o[oi].write("    Simulation-only:\n")
        for obj in sim_only[(ei, ri, oi)]:
            l="      {} :: pt/eta/phi = {:4d} {:4d} {:4d}"
            if obj in sim_input_lookup: 
              ll=" :: sim (clk,link)={}\n".format(sim_input_lookup[obj])
            else: 
              ll="\n"
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
